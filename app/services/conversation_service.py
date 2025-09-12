"""
Servicio para manejo de conversaciones y generación de respuestas con IA real
"""

from typing import Dict, Any, List, Optional, Tuple
import openai
from datetime import datetime
import tiktoken
from sqlalchemy.orm import Session

from app.models.schemas import (
    QueryRequest, 
    ConceptualResponse, 
    AccionalResponse,
    ClarificationQuestion
)
from app.db.vector_store import VectorStore
from app.services.ingestion_service import IngestionService
from app.services.memory_service import MemoryService
from app.db.database import SessionLocal
from app.core.config import settings

class ConversationService:
    """
    Servicio encargado de procesar consultas y generar respuestas estratégicas con IA
    """
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.ingestion_service = IngestionService()
        self.memory_service = MemoryService()
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.conversation_memory: Dict[str, List[Dict]] = {}
        self.encoding = tiktoken.encoding_for_model(settings.OPENAI_MODEL)
    
    async def analyze_ambiguity(self, message: str) -> bool:
        """
        Analiza si un mensaje es ambiguo y requiere clarificación usando IA
        con umbrales más permisivos
        """
        
        personality_config = self.ingestion_service.get_personality_config()
        
        # If personality is configured, use its protocol for ambiguity analysis
        if personality_config["status"] == "personality_configured":
            # With personality configured, we should follow the protocol directly
            # Only ask for clarification if the message is extremely minimal (less than 3 words)
            return len(message.split()) < 3
        
        # Mensajes muy cortos (menos de 4 palabras) siempre requieren clarificación
        if len(message.split()) < 4:
            return True
        
        # Si el mensaje contiene palabras clave de ambigüedad
        ambiguity_keywords = [
            'estrategia', 'negocio', 'software', 'empresa', 'startup',
            'qué hacer', 'consejo', 'recomendación', 'idea'
        ]
        
        message_lower = message.lower()
        has_ambiguity_keywords = any(keyword in message_lower for keyword in ambiguity_keywords)
        
        # Si es muy general pero tiene palabras clave, necesita clarificación
        if len(message.split()) < 8 and has_ambiguity_keywords:
            return True
        
        # Para otros casos, usar IA con umbral más permisivo
        prompt = f"""
        Eres un asistente que analiza si las consultas son demasiado generales para responder específicamente.
        Responde SOLO con "True" o "False" sin comillas.
        
        Considera la consulta ambigua SOLO si:
        1. Es extremadamente vaga (menos de 5 palabras)
        2. No menciona ningún contexto específico
        3. Pide "consejo" o "estrategia" sin especificar área
        
        Si la consulta da aunque sea un contexto mínimo (ej: "software", "SaaS"), responde "False".
        
        Consulta: "{message}"
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().lower()
            return result == "true"
            
        except Exception:
            # Fallback menos estricto
            return len(message.split()) < 5
    
    async def _analyze_ambiguity_with_personality(self, message: str, personality_config: Dict[str, Any]) -> bool:
        """
        Analiza ambigüedad usando el protocolo de personalidad configurado
        """
        
        personality_text = personality_config.get("full_personality_text", "")
        
        prompt = f"""
        Tienes configurado el siguiente protocolo de personalidad:
        
        {personality_text}
        
        Basándote en este protocolo, analiza si la siguiente consulta requiere clarificación según las reglas establecidas en tu personalidad.
        
        Responde SOLO con "True" si necesita clarificación o "False" si puedes proceder directamente.
        
        Consulta del usuario: "{message}"
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Eres un agente que sigue estrictamente el protocolo de personalidad configurado."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().lower()
            return result == "true"
            
        except Exception as e:
            print(f"❌ Error analizando ambigüedad con personalidad: {e}")
            # Fallback to original method
            return len(message.split()) < 5
    
    async def generate_clarification_questions(self, message: str) -> List[ClarificationQuestion]:
        """
        Genera preguntas de clarificación concisas y enfocadas
        """
        
        personality_config = self.ingestion_service.get_personality_config()
        
        if personality_config["status"] == "personality_configured":
            return await self._generate_clarification_with_personality(message, personality_config)
        
        # Original clarification generation as fallback
        prompt = f"""
        La siguiente consulta necesita clarificación: "{message}"
        
        Genera EXACTAMENTE 2 preguntas de clarificación que sean:
        1. Muy específicas y directas
        2. Centradas en obtener la información más crítica
        3. Con opciones de respuesta concisas (máximo 3 opciones)
        
        Formato:
        Pregunta: [pregunta breve]
        Contexto: [contexto muy breve]
        Opciones: [opción 1], [opción 2], [opción 3]
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            questions = self._parse_clarification_questions(content)
            return questions[:2]  # Solo 2 preguntas máximo
            
        except Exception as e:
            # Preguntas de fallback más concisas
            return [
                ClarificationQuestion(
                    question="¿Qué tipo específico de software desarrollas?",
                    context="Para darte una estrategia precisa",
                    suggested_answers=["SaaS", "App móvil", "Software empresarial"]
                ),
                ClarificationQuestion(
                    question="¿Cuál es tu objetivo principal?",
                    context="Para enfocar la estrategia correctamente",
                    suggested_answers=["Crecimiento rápido", "Rentabilidad", "Innovación"]
                )
            ]
    
    async def _generate_clarification_with_personality(self, message: str, personality_config: Dict[str, Any]) -> List[ClarificationQuestion]:
        """
        Genera preguntas de clarificación usando el protocolo de personalidad
        """
        
        personality_text = personality_config.get("full_personality_text", "")
        
        prompt = f"""
        Tienes configurado el siguiente protocolo de personalidad:
        
        {personality_text}
        
        Siguiendo EXACTAMENTE este protocolo, genera las preguntas de clarificación apropiadas para la consulta: "{message}"
        
        Usa el estilo, tono y metodología especificados en tu protocolo.
        
        Formato:
        Pregunta: [pregunta según tu protocolo]
        Contexto: [contexto según tu estilo]
        Opciones: [opción 1], [opción 2], [opción 3]
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Sigues estrictamente el protocolo de personalidad configurado para generar preguntas de clarificación."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            questions = self._parse_clarification_questions(content)
            return questions[:3]  # Hasta 3 preguntas según el protocolo
            
        except Exception as e:
            print(f"❌ Error generando clarificación con personalidad: {e}")
            # Fallback to default questions
            return [
                ClarificationQuestion(
                    question="¿Podrías ser más específico sobre tu situación?",
                    context="Para brindarte la mejor orientación",
                    suggested_answers=["Contexto empresarial", "Contexto personal", "Contexto técnico"]
                )
            ]
    
    def _parse_clarification_questions(self, content: str) -> List[ClarificationQuestion]:
        """
        Parsea la respuesta de OpenAI en objetos ClarificationQuestion
        """
        questions = []
        lines = content.split('\n')
        current_question = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Pregunta:'):
                if current_question:
                    questions.append(current_question)
                current_question = ClarificationQuestion(
                    question=line.replace('Pregunta:', '').strip(),
                    context="",
                    suggested_answers=[]
                )
            elif line.startswith('Contexto:') and current_question:
                current_question.context = line.replace('Contexto:', '').strip()
            elif line.startswith('Opciones:') and current_question:
                options = line.replace('Opciones:', '').strip().split(',')
                current_question.suggested_answers = [opt.strip() for opt in options if opt.strip()]
        
        if current_question:
            questions.append(current_question)
            
        return questions
    
    async def generate_strategic_response(
        self, 
        message: str, 
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        history_context: Optional[List[Dict]] = None  # Added history_context parameter
    ) -> Tuple[ConceptualResponse, AccionalResponse]:
        """
        Genera respuesta estratégica completa (conceptual + accional) usando IA
        incluso con información limitada
        """
        
        print(f"🔄 [DEBUG] Starting generate_strategic_response for session: {session_id}")
        print(f"🔄 [DEBUG] History context provided: {len(history_context) if history_context else 0} messages")
        
        try:
            db = SessionLocal()
            print(f"✅ [DEBUG] Database session created successfully")
        except Exception as e:
            print(f"❌ [DEBUG] Error creating database session: {e}")
            # Return fallback without database
            return await self._generate_fallback_responses(message)
        
        try:
            try:
                self.memory_service.add_message(db, session_id, "user", message)
                print(f"✅ [DEBUG] User message added to memory")
            except Exception as e:
                print(f"❌ [DEBUG] Error adding message to memory: {e}")
                # Continue without memory
            
            try:
                relevant_context = await self._search_relevant_context(message)
                print(f"✅ [DEBUG] Context search completed: {len(relevant_context)} results")
            except Exception as e:
                print(f"❌ [DEBUG] Error searching context: {e}")
                relevant_context = []
            
            try:
                if history_context is None:
                    full_context = self.memory_service.get_full_context_for_ai(db, session_id, memory_limit=200)
                    conversation_history = full_context.get("messages", [])
                    print(f"✅ [DEBUG] Fetched FULL conversation context: {len(conversation_history)} messages")
                else:
                    conversation_history = history_context
                    print(f"✅ [DEBUG] Using provided history context: {len(conversation_history)} messages")
                
                key_info = self.memory_service.extract_key_info(db, session_id, message)
                print(f"✅ [DEBUG] Memory retrieval completed")
            except Exception as e:
                print(f"❌ [DEBUG] Error retrieving memory: {e}")
                conversation_history = history_context or []
                key_info = {}
            
            try:
                personality_config = self.ingestion_service.get_personality_config()
                if not isinstance(personality_config, dict):
                    personality_config = {"status": "no_personality_configured", "files": []}
                print(f"✅ [DEBUG] Personality config retrieved: {personality_config.get('status', 'unknown')}")
            except Exception as e:
                print(f"❌ [DEBUG] Error getting personality config: {e}")
                personality_config = {"status": "no_personality_configured", "files": []}
            
            try:
                conceptual = await self._generate_conceptual_response(
                    message, relevant_context, conversation_history, personality_config, key_info
                )
                print(f"✅ [DEBUG] Conceptual response generated")
            except Exception as e:
                print(f"❌ [DEBUG] Error generating conceptual response: {e}")
                conceptual = ConceptualResponse(
                    content="Error generando respuesta conceptual. Intenta nuevamente.",
                    sources=[],
                    confidence=0.1
                )
            
            try:
                accional = await self._generate_accional_response(
                    message, relevant_context, conceptual.content, personality_config
                )
                print(f"✅ [DEBUG] Accional response generated")
            except Exception as e:
                print(f"❌ [DEBUG] Error generating accional response: {e}")
                accional = AccionalResponse(
                    content="Error generando plan de acción. Intenta nuevamente.",
                    priority="media",
                    timeline="Indefinido"
                )
            
            try:
                full_response = f"## Análisis Conceptual\n{conceptual.content}\n\n## Plan de Acción\n{accional.content}"
                self.memory_service.add_message(db, session_id, "assistant", full_response)
                print(f"✅ [DEBUG] Assistant response added to memory")
            except Exception as e:
                print(f"❌ [DEBUG] Error adding assistant response to memory: {e}")
                # Continue without saving to memory
            
            print(f"✅ [DEBUG] generate_strategic_response completed successfully")
            return conceptual, accional
            
        except Exception as e:
            print(f"❌ [DEBUG] Unexpected error in generate_strategic_response: {e}")
            return await self._generate_fallback_responses(message)
        finally:
            try:
                db.close()
                print(f"✅ [DEBUG] Database session closed")
            except Exception as e:
                print(f"❌ [DEBUG] Error closing database session: {e}")

    async def _generate_fallback_responses(self, message: str) -> Tuple[ConceptualResponse, AccionalResponse]:
        """
        Genera respuestas de fallback cuando hay errores en el sistema principal
        """
        print(f"🔄 [DEBUG] Generating fallback responses")
        
        fallback_conceptual = ConceptualResponse(
            content="Estoy experimentando dificultades técnicas temporales. Tu consulta es importante y la procesaré tan pronto como sea posible.",
            sources=[],
            confidence=0.1
        )
        
        fallback_accional = AccionalResponse(
            content="Por favor, intenta enviar tu consulta nuevamente en unos momentos.",
            priority="media",
            timeline="Inmediato"
        )
        
        return fallback_conceptual, fallback_accional

    async def _search_relevant_context(self, message: str) -> List[Dict[str, Any]]:
        """
        Busca contexto relevante en la base vectorial
        """
        if not hasattr(self.vector_store, 'store') or self.vector_store.store.index is None:
            await self.vector_store.initialize()
        
        try:
            results = await self.vector_store.similarity_search(message, top_k=5)
            print(f"🔍 Encontrados {len(results)} documentos relevantes para: '{message[:50]}...'")
            return results
        except Exception as e:
            print(f"❌ Error buscando contexto: {e}")
            return []

    def _get_conversation_history(self, session_id: str) -> List[Dict]:
        """
        Recupera el historial de conversación de una sesión
        """
        return self.conversation_memory.get(session_id, [])
    
    def _build_conversation_prompt(self, message: str, context: List[Dict], history: List[Dict], response_type: str, key_info: Dict[str, Any] = None) -> str:
        """
        Construye el prompt para la generación de respuestas
        """
        context_text = ""
        if context:
            context_text = "## Contexto relevante de tus documentos:\n"
            for i, doc in enumerate(context, 1):
                content = doc.get('content', '')[:500]  # Limit context length
                source = doc.get('source', 'documento')
                context_text += f"{i}. **Fuente: {source}**\n{content}...\n\n"
        
        history_text = ""
        if history and len(history) > 0:
            history_text = "## HISTORIAL COMPLETO DE CONVERSACIÓN (RECUERDA TODA ESTA INFORMACIÓN):\n"
            for msg in history:  # Usar TODOS los mensajes, no solo [-8:]
                role_label = "Usuario" if msg.get("role") == "user" else "Erasmo (tú)"
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                history_text += f"**{role_label}** ({timestamp}): {content}\n\n"
            history_text += "---\n\n"
        
        key_info_text = ""
        if key_info:
            key_info_text = "## INFORMACIÓN CLAVE QUE YA CONOCES (NO PREGUNTES ESTO NUEVAMENTE):\n"
            if key_info.get("company_name"):
                key_info_text += f"- Empresa: {key_info['company_name']}\n"
            if key_info.get("industry"):
                key_info_text += f"- Industria: {key_info['industry']}\n"
            if key_info.get("objectives"):
                key_info_text += f"- Objetivos: {', '.join(key_info['objectives'])}\n"
            if key_info.get("detected_topics"):
                key_info_text += f"- Temas tratados: {', '.join(key_info['detected_topics'])}\n"
            key_info_text += "\n"
        
        extracted_info = self._extract_info_from_history(history)
        if extracted_info:
            key_info_text += "## INFORMACIÓN ADICIONAL DEL HISTORIAL COMPLETO:\n"
            for key, value in extracted_info.items():
                key_info_text += f"- {key}: {value}\n"
            key_info_text += "\n"
        
        if response_type == "conceptual":
            prompt_specific = """
            Como Erasmo, el estratega experto, genera una respuesta conceptual que:
            1. Use ESPECÍFICAMENTE la información de los documentos proporcionados
            2. RECUERDE y referencie TODA la información previa de la conversación completa (NO REPITAS PREGUNTAS YA RESPONDIDAS)
            3. Explique el marco teórico relevante basado en TU conocimiento indexado
            4. Analice por qué es importante esta situación según tus fuentes
            5. Establezca conexiones con principios estratégicos de tus documentos
            6. Si ya conoces información del usuario (empresa, industria, etc.), úsala directamente y refiérela específicamente
            
            CRÍTICO: NO pidas información que ya tienes del historial conversacional completo.
            IMPORTANTE: Basa tu respuesta principalmente en el contexto de documentos proporcionado y TODA la información recordada.
            DEBES DEMOSTRAR que recuerdas información específica mencionada anteriormente.
            Responde en formato Markdown, siendo claro y estratégico.
            """
        else:  # accional
            prompt_specific = """
            Como Erasmo, el estratega experto, genera un plan de acción práctico que:
            1. Use las recomendaciones específicas de tus documentos indexados
            2. CONSIDERE TODA la información previa de la conversación completa
            3. Desglose pasos concretos basados en tu conocimiento
            4. Establezca prioridades según las mejores prácticas de tus fuentes
            5. Defina un timeline realista basado en experiencias documentadas
            6. Incorpore TODA la información ya conocida del usuario del historial completo
            
            CRÍTICO: NO repitas preguntas sobre información que ya tienes en el historial completo.
            IMPORTANTE: Fundamenta las acciones en el conocimiento de tus documentos y TODO el contexto conversacional.
            DEBES REFERENCIAR información específica del historial para demostrar continuidad.
            Responde en formato Markdown, siendo específico y accionable.
            """
        
        return f"""
        {key_info_text}
        {context_text}
        {history_text}
        
        {prompt_specific}
        
        Consulta actual: {message}
        """

    def _extract_info_from_history(self, history: List[Dict]) -> Dict[str, str]:
        """
        Extrae información clave del historial conversacional para evitar preguntas repetitivas
        """
        extracted = {}
        
        if not history:
            return extracted
        
        for msg in history:
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                
                if "empresa" in content or "compañía" in content:
                    words = content.split()
                    for i, word in enumerate(words):
                        if word in ["empresa", "compañía", "negocio"] and i + 1 < len(words):
                            extracted["Empresa mencionada"] = words[i + 1].title()
                            break
                
                sectors = ["tecnología", "software", "saas", "fintech", "ecommerce", "retail", "salud", "educación", "marketing", "consultoría"]
                for sector in sectors:
                    if sector in content:
                        extracted["Sector/Industria"] = sector.title()
                        break
                
                objectives = ["crecer", "expandir", "mejorar", "optimizar", "aumentar", "reducir", "lanzar"]
                for obj in objectives:
                    if obj in content:
                        extracted["Objetivo mencionado"] = f"Busca {obj}"
                        break
        
        return extracted
    
    async def _generate_conceptual_response(
        self, 
        message: str, 
        context: List[Dict], 
        history: List[Dict],
        personality_config: Dict[str, Any],
        key_info: Dict[str, Any] = None
    ) -> ConceptualResponse:
        """
        Genera respuesta a nivel conceptual (por qué) usando OpenAI
        incluso con información limitada
        """
        
        if personality_config["status"] == "personality_configured":
            personality_text = personality_config.get("full_personality_text", "")
            if len(personality_text) > 2000:
                personality_text = personality_text[:2000] + "..."
            
            system_prompt = f"""
            Tienes configurada la siguiente personalidad y protocolo:
            
            {personality_text}
            
            Debes seguir EXACTAMENTE este protocolo, estilo y tono en todas tus respuestas.
            Eres un estratega experto que sigue las reglas y metodología especificadas en tu configuración de personalidad.
            
            IMPORTANTE: 
            - RECUERDA información de conversaciones anteriores
            - Si el usuario ya te dio información (como nombre de empresa, industria, etc.), úsala y refiérela
            - NO pidas información que ya tienes del historial conversacional
            - Sigue tu protocolo de indagación específico solo para información nueva que necesites
            
            MANTÉN TUS RESPUESTAS CONCISAS Y DIRECTAS (máximo 800 palabras).
            """
        else:
            system_prompt = "Eres Erasmo, un estratega experto con amplio conocimiento en negocios, liderazgo y toma de decisiones estratégicas. RECUERDA información de conversaciones anteriores. Mantén respuestas concisas (máximo 800 palabras)."
        
        prompt = self._build_conversation_prompt(message, context, history, "conceptual", key_info)
        
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,  # Aumentado de 400 a 800 para respuestas más completas
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else self._count_tokens(content)
            
            sources = []
            if context:
                sources = [doc.get('source', '') for doc in context if doc.get('source')]
            
            return ConceptualResponse(
                content=content,
                sources=sources if sources else ["protocolo_personalidad", "conocimiento_estratégico"],
                confidence=0.8 if personality_config["status"] == "personality_configured" else 0.7
            )
            
        except Exception as e:
            return ConceptualResponse(
                content=f"## Análisis Conceptual\n\nLo siento, estoy teniendo dificultades técnicas. Por favor, intentanuevamente.\n\nError: {str(e)}",
                sources=[],
                confidence=0.1
            )

    async def _generate_accional_response(
        self, 
        message: str, 
        context: List[Dict],
        conceptual_content: str,
        personality_config: Dict[str, Any]
    ) -> AccionalResponse:
        """
        Genera respuesta a nivel accional (qué hacer) usando OpenAI
        """
        
        if personality_config["status"] == "personality_configured":
            personality_text = personality_config.get("full_personality_text", "")
            if len(personality_text) > 1500:
                personality_text = personality_text[:1500] + "..."
            
            system_prompt = f"""
            Tienes configurada la siguiente personalidad y protocolo:
            
            {personality_text}
            
            Debes seguir EXACTAMENTE este protocolo, estilo y tono para generar planes de acción.
            Usa tu metodología específica de indagación y diagnóstico estratégico.
            
            MANTÉN TUS RESPUESTAS CONCISAS Y DIRECTAS (máximo 600 palabras).
            """
        else:
            system_prompt = "Eres Erasmo, un estratega experto en crear planes de acción efectivos. Mantén respuestas concisas (máximo 600 palabras)."
        
        if len(conceptual_content) > 500:
            conceptual_content = conceptual_content[:500] + "..."
        
        prompt = f"""
        Basado en el siguiente análisis conceptual:
        {conceptual_content}
        
        Y la consulta original: "{message}"
        
        Siguiendo tu protocolo configurado:
        1. Genera el plan de acción según tu metodología
        2. Usa tu sistema de indagación estratégica si necesitas profundizar
        3. Mantén el tono y estilo de tu personalidad configurada
        4. RECUERDA información previa de la conversación
        
        Respuesta CONCISA en Markdown siguiendo tu protocolo.
        MÁXIMO 600 palabras.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=700,  # Aumentado de 500 a 700 para planes más detallados
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            priority = "media"
            if any(word in content.lower() for word in ["urgente", "inmediato", "crítico", "prioridad alta"]):
                priority = "alta"
            elif any(word in content.lower() for word in ["largo plazo", "eventualmente", "cuando sea posible"]):
                priority = "baja"
                
            timeline = "2-3 semanas"  # Valor por defecto
            if "días" in content.lower() or "semana" in content.lower():
                timeline = "1-2 semanas"
            elif "mes" in content.lower():
                timeline = "3-4 semanas"
            
            return AccionalResponse(
                content=content,
                priority=priority,
                timeline=timeline
            )
            
        except Exception as e:
            return AccionalResponse(
                content=f"## Plan de Acción\n\nLo siento, estoy teniendo dificultades técnicas. Por favor, intenta nuevamente.\n\nError: {str(e)}",
                priority="media",
                timeline="Indefinido"
            )
    
    def _count_tokens(self, text: str) -> int:
        """Cuenta tokens en un texto"""
        return len(self.encoding.encode(text))
    
    def _update_conversation_memory(
        self, 
        session_id: str, 
        message: str,
        conceptual: ConceptualResponse,
        accional: AccionalResponse
    ):
        """
        Actualiza la memoria de conversación
        """
        
        if session_id not in self.conversation_memory:
            self.conversation_memory[session_id] = []
        
        self.conversation_memory[session_id].append({
            "timestamp": datetime.now().isoformat(),
            "user_message": message,
            "conceptual_response": conceptual.content,
            "accional_response": accional.content
        })
        
        if len(self.conversation_memory[session_id]) > settings.CONVERSATION_MEMORY_SIZE:
            self.conversation_memory[session_id] = self.conversation_memory[session_id][-settings.CONVERSATION_MEMORY_SIZE:]
