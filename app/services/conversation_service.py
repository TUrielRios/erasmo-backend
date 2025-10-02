"""
Servicio mejorado para manejo de conversaciones con seguimiento estricto de instrucciones
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
    ClarificationQuestion,
    DocumentCategory
)
from app.db.vector_store import VectorStore
from app.services.ingestion_service import IngestionService
from app.services.memory_service import MemoryService
from app.db.database import SessionLocal
from app.core.config import settings

class ConversationService:
    """
    Servicio mejorado para procesamiento de consultas con seguimiento estricto de instrucciones
    y uso prioritario de fuentes de conocimiento personalizadas
    """
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.ingestion_service = IngestionService()
        self.memory_service = MemoryService()
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.conversation_memory: Dict[str, List[Dict]] = {}
        self.encoding = tiktoken.encoding_for_model(settings.OPENAI_MODEL)
    
    async def analyze_ambiguity(self, message: str, user_id: int = None) -> bool:
        """
        Analiza si un mensaje es ambiguo usando instrucciones personalizadas por compañía
        """
        db = SessionLocal()
        try:
            company_instructions = await self._get_company_instructions(db, user_id)
            
            if company_instructions:
                return await self._analyze_ambiguity_with_instructions(message, company_instructions)
            
            # Fallback to original logic
            if len(message.split()) < 4:
                return True
            
            ambiguity_keywords = [
                'estrategia', 'negocio', 'software', 'empresa', 'startup',
                'qué hacer', 'consejo', 'recomendación', 'idea'
            ]
            
            message_lower = message.lower()
            has_ambiguity_keywords = any(keyword in message_lower for keyword in ambiguity_keywords)
            
            if len(message.split()) < 8 and has_ambiguity_keywords:
                return True
            
            return len(message.split()) < 5
            
        finally:
            db.close()
    
    async def _analyze_ambiguity_with_instructions(self, message: str, instructions: List[Dict]) -> bool:
        """
        Analiza ambigüedad usando instrucciones específicas de la compañía
        """
        instruction_text = self._compile_instructions(instructions)
        
        prompt = f"""
        Siguiendo estas instrucciones específicas:
        
        {instruction_text}
        
        Analiza si la siguiente consulta requiere clarificación según las reglas establecidas.
        
        Responde SOLO con "True" si necesita clarificación o "False" si puedes proceder directamente.
        
        Consulta del usuario: "{message}"
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "system", "content": "Sigues estrictamente las instrucciones proporcionadas para determinar si una consulta necesita clarificación."}, {"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip().lower()
            return result == "true"
            
        except Exception as e:
            print(f"❌ Error analizando ambigüedad con instrucciones: {e}")
            return len(message.split()) < 5

    async def generate_clarification_questions(self, message: str, user_id: int = None) -> List[ClarificationQuestion]:
        """
        Genera preguntas de clarificación usando instrucciones personalizadas
        """
        db = SessionLocal()
        try:
            company_instructions = await self._get_company_instructions(db, user_id)
            
            if company_instructions:
                return await self._generate_clarification_with_instructions(message, company_instructions)
            
            # Fallback to original logic
            return await self._generate_default_clarification(message)
            
        finally:
            db.close()
    
    async def _generate_clarification_with_instructions(self, message: str, instructions: List[Dict]) -> List[ClarificationQuestion]:
        """
        Genera preguntas de clarificación siguiendo instrucciones específicas
        """
        instruction_text = self._compile_instructions(instructions)
        
        prompt = f"""
        Siguiendo estas instrucciones específicas:
        
        {instruction_text}
        
        Genera preguntas de clarificación apropiadas para la consulta: "{message}"
        
        Usa el estilo, tono y metodología especificados en las instrucciones.
        
        Formato:
        Pregunta: [pregunta según las instrucciones]
        Contexto: [contexto según el estilo]
        Opciones: [opción 1], [opción 2], [opción 3]
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "system", "content": "Sigues estrictamente las instrucciones proporcionadas para generar preguntas de clarificación."}, {"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            questions = self._parse_clarification_questions(content)
            return questions[:3]
            
        except Exception as e:
            print(f"❌ Error generando clarificación con instrucciones: {e}")
            return await self._generate_default_clarification(message)

    async def generate_strategic_response(
        self, 
        message: str, 
        session_id: str,
        user_id: int,
        context: Optional[Dict[str, Any]] = None,
        history_context: Optional[List[Dict]] = None
    ) -> Tuple[ConceptualResponse, AccionalResponse]:
        """
        Genera respuesta estratégica usando fuentes de conocimiento e instrucciones personalizadas
        """
        print(f"🔄 [DEBUG] Starting enhanced generate_strategic_response for session: {session_id}, user: {user_id}")
        
        db = SessionLocal()
        try:
            user_company_data = await self._get_user_company_data(db, user_id)
            company_knowledge = await self._get_company_knowledge(db, user_company_data.get('company_id'))
            company_instructions = await self._get_company_instructions(db, user_id)
            ai_config = await self._get_ai_configuration(db, user_company_data.get('company_id'))
            
            print(f"✅ [DEBUG] Company data loaded: {len(company_knowledge)} knowledge docs, {len(company_instructions)} instruction docs")
            
            # Add message to memory
            try:
                self.memory_service.add_message(db, session_id, "user", message)
                print(f"✅ [DEBUG] User message added to memory")
            except Exception as e:
                print(f"❌ [DEBUG] Error adding message to memory: {e}")
            
            relevant_context = await self._search_prioritized_context(
                message, 
                company_knowledge, 
                company_id=user_company_data.get('company_id')
            )
            print(f"✅ [DEBUG] Prioritized context search completed: {len(relevant_context)} results")
            
            # Get conversation history
            try:
                if history_context is None:
                    full_context = self.memory_service.get_full_context_for_ai(db, session_id, memory_limit=200)
                    conversation_history = full_context.get("messages", [])
                    print(f"✅ [DEBUG] Fetched conversation context: {len(conversation_history)} messages")
                else:
                    conversation_history = history_context
                
                key_info = self.memory_service.extract_key_info(db, session_id, message)
                print(f"✅ [DEBUG] Memory retrieval completed")
            except Exception as e:
                print(f"❌ [DEBUG] Error retrieving memory: {e}")
                conversation_history = history_context or []
                key_info = {}
            
            try:
                conceptual = await self._generate_conceptual_with_instructions(
                    message, relevant_context, conversation_history, 
                    company_instructions, company_knowledge, key_info, ai_config, user_company_data
                )
                print(f"✅ [DEBUG] Conceptual response generated with instructions")
            except Exception as e:
                print(f"❌ [DEBUG] Error generating conceptual response: {e}")
                conceptual = ConceptualResponse(
                    content="Error generando respuesta conceptual. Intenta nuevamente.",
                    sources=[],
                    confidence=0.1
                )
            
            try:
                accional = await self._generate_accional_with_instructions(
                    message, relevant_context, conceptual.content, 
                    company_instructions, ai_config
                )
                print(f"✅ [DEBUG] Accional response generated with instructions")
            except Exception as e:
                print(f"❌ [DEBUG] Error generating accional response: {e}")
                accional = AccionalResponse(
                    content="Error generando plan de acción. Intenta nuevamente.",
                    priority="media",
                    timeline="Indefinido"
                )
            
            # Save assistant response
            try:
                full_response = f"## Análisis Conceptual\n{conceptual.content}\n\n## Plan de Acción\n{accional.content}"
                self.memory_service.add_message(db, session_id, "assistant", full_response)
                print(f"✅ [DEBUG] Assistant response added to memory")
            except Exception as e:
                print(f"❌ [DEBUG] Error adding assistant response to memory: {e}")
            
            print(f"✅ [DEBUG] Enhanced generate_strategic_response completed successfully")
            return conceptual, accional
            
        except Exception as e:
            print(f"❌ [DEBUG] Unexpected error in enhanced generate_strategic_response: {e}")
            return await self._generate_fallback_responses(message)
        finally:
            db.close()

    async def _get_user_company_data(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Obtiene datos de la compañía del usuario
        """
        try:
            from app.services.auth_service import AuthService
            user = AuthService.get_user_with_company(db, user_id)
            
            if user and user.company:
                return {
                    "company_id": user.company.id,
                    "company_name": user.company.name,
                    "industry": user.company.industry,
                    "sector": user.company.sector,
                    "work_area": user.work_area
                }
            return {}
        except Exception as e:
            print(f"❌ Error getting user company data: {e}")
            return {}

    async def _get_company_knowledge(self, db: Session, company_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene documentos de fuentes de conocimiento de la compañía
        """
        if not company_id:
            return []
        
        try:
            from app.services.company_service import CompanyDocumentService
            knowledge_docs = CompanyDocumentService.get_documents_by_priority(
                db, company_id, DocumentCategory.KNOWLEDGE_BASE, max_priority=10
            )
            
            knowledge_content = []
            for doc in knowledge_docs:
                content = CompanyDocumentService.get_document_content(db, company_id, doc.id)
                if content:
                    knowledge_content.append({
                        "filename": doc.filename,
                        "content": content,
                        "priority": doc.priority,
                        "description": doc.description,
                        "category": "knowledge_base"
                    })
            
            return knowledge_content
        except Exception as e:
            print(f"❌ Error getting company knowledge: {e}")
            return []

    async def _get_company_instructions(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene documentos de instrucciones de la compañía del usuario
        """
        try:
            user_data = await self._get_user_company_data(db, user_id)
            company_id = user_data.get('company_id')
            
            if not company_id:
                return []
            
            from app.services.company_service import CompanyDocumentService
            instruction_docs = CompanyDocumentService.get_documents_by_priority(
                db, company_id, DocumentCategory.INSTRUCTIONS, max_priority=10
            )
            
            instructions_content = []
            for doc in instruction_docs:
                content = CompanyDocumentService.get_document_content(db, company_id, doc.id)
                if content:
                    instructions_content.append({
                        "filename": doc.filename,
                        "content": content,
                        "priority": doc.priority,
                        "description": doc.description,
                        "category": "instructions"
                    })
            
            return instructions_content
        except Exception as e:
            print(f"❌ Error getting company instructions: {e}")
            return []

    async def _get_ai_configuration(self, db: Session, company_id: int) -> Optional[Any]:
        """
        Obtiene configuración de IA de la compañía
        """
        if not company_id:
            return None
        
        try:
            from app.services.ai_configuration_service import AIConfigurationService
            return AIConfigurationService.get_by_company_id(db, company_id)
        except Exception as e:
            print(f"❌ Error getting AI configuration: {e}")
            return None

    async def _search_prioritized_context(self, message: str, company_knowledge: List[Dict], company_id: int = None) -> List[Dict[str, Any]]:
        """
        Busca contexto usando búsqueda vectorial semántica en Pinecone
        """
        prioritized_context = []
        
        try:
            if not hasattr(self.vector_store, 'store') or self.vector_store.store.index is None:
                await self.vector_store.initialize()
            
            # Búsqueda vectorial semántica en Pinecone - encuentra documentos relevantes basándose en el significado
            vector_results = await self.vector_store.similarity_search(
                message, 
                top_k=15,  # Buscar más documentos para asegurar que encontramos todos los valores
                company_id=company_id
            )
            
            print(f"🔍 [DEBUG] Vector search found {len(vector_results)} relevant documents")
            
            # Agregar resultados de búsqueda vectorial
            for result in vector_results:
                content = result.get('content', '')
                source = result.get('source', 'conocimiento_vectorial')
                score = result.get('score', 0.0)
                
                prioritized_context.append({
                    'content': content,
                    'source': source,
                    'priority': 1,  # Alta prioridad para resultados vectoriales relevantes
                    'category': 'vector_search',
                    'relevance_score': score
                })
            
            print(f"✅ [DEBUG] Added {len(prioritized_context)} documents from vector search")
            
        except Exception as e:
            print(f"❌ Error in vector search: {e}")
        
        for doc in company_knowledge:
            content = doc.get('content', '')
            # Solo agregar si no está ya en los resultados vectoriales
            if not any(ctx.get('content') == content for ctx in prioritized_context):
                prioritized_context.append({
                    'content': content[:2500],
                    'source': f"conocimiento_{doc['filename']}",
                    'priority': doc.get('priority', 5),
                    'category': 'company_knowledge'
                })
        
        # Ordenar por relevancia (score de búsqueda vectorial) y prioridad
        prioritized_context.sort(key=lambda x: (x.get('relevance_score', 0.0), -x.get('priority', 5)), reverse=True)
        
        print(f"📊 [DEBUG] Total context documents: {len(prioritized_context)}")
        
        # Retornar los documentos más relevantes
        return prioritized_context[:10]

    def _is_content_relevant(self, message: str, content: str) -> bool:
        """
        Determina si el contenido es relevante para el mensaje
        """
        message_words = set(message.lower().split())
        content_words = set(content.lower().split())
        
        # Simple relevance check based on word overlap
        overlap = len(message_words.intersection(content_words))
        return overlap >= 2 or len(message_words.intersection(content_words)) / len(message_words) > 0.2

    def _compile_instructions(self, instructions: List[Dict]) -> str:
        """
        Compila las instrucciones en un texto coherente
        """
        if not instructions:
            return "No hay instrucciones específicas configuradas."
        
        compiled = "INSTRUCCIONES ESPECÍFICAS A SEGUIR AL PIE DE LA LETRA:\n\n"
        
        for i, instruction in enumerate(instructions, 1):
            priority = instruction.get('priority', 5)
            filename = instruction.get('filename', f'instruccion_{i}')
            content = instruction.get('content', '')
            
            compiled += f"## INSTRUCCIÓN {i} (Prioridad {priority}) - {filename}\n"
            compiled += f"{content}\n\n"
        
        compiled += "\nDEBES SEGUIR ESTAS INSTRUCCIONES EXACTAMENTE COMO ESTÁN ESCRITAS."
        return compiled

    async def _generate_conceptual_with_instructions(
        self, 
        message: str, 
        context: List[Dict], 
        history: List[Dict],
        instructions: List[Dict],
        knowledge: List[Dict],
        key_info: Dict[str, Any],
        ai_config: Any,
        user_company_data: Dict[str, Any]
    ) -> ConceptualResponse:
        """
        Genera respuesta conceptual siguiendo instrucciones específicas y usando conocimiento prioritario
        """
        company_name = user_company_data.get('company_name', 'tu empresa')
        industry = user_company_data.get('industry', '')
        
        instruction_text = self._compile_instructions(instructions)
        knowledge_text = self._compile_knowledge(knowledge)
        
        system_prompt = f"""
        ERES UN ASISTENTE DE IA PERSONALIZADO PARA {company_name.upper()}.
        
        INSTRUCCIONES CRÍTICAS - DEBES SEGUIR AL PIE DE LA LETRA:
        {instruction_text}
        
        FUENTES DE CONOCIMIENTO PRIORITARIAS (USA ESTAS PRIMERO):
        {knowledge_text}
        
        INFORMACIÓN DE LA EMPRESA:
        - Empresa: {company_name}
        - Industria: {industry}
        - Sector: {user_company_data.get('sector', '')}
        
        REGLAS ESTRICTAS:
        1. SIEMPRE sigue las instrucciones específicas proporcionadas
        2. USA PRIMERO el conocimiento de las fuentes prioritarias
        3. Si las fuentes no son suficientes, ENTONCES usa conocimiento general
        4. RECUERDA información de conversaciones anteriores
        5. ADAPTA tu respuesta al contexto específico de {company_name}
        
        Mantén respuestas concisas y directas.
        """
        
        prompt = self._build_enhanced_conversation_prompt(message, context, history, "conceptual", key_info)
        
        model_name = ai_config.model_name if ai_config else settings.OPENAI_MODEL
        temperature = float(ai_config.temperature) if ai_config else 0.7
        max_tokens = (ai_config.max_tokens // 2) if ai_config else 800
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            
            sources = []
            for doc in knowledge:
                sources.append(f"conocimiento_{doc['filename']}")
            for doc in instructions:
                sources.append(f"instrucciones_{doc['filename']}")
            
            if not sources:
                sources = ["configuracion_personalizada"]
            
            return ConceptualResponse(
                content=content,
                sources=sources,
                confidence=0.95 if knowledge and instructions else 0.8
            )
            
        except Exception as e:
            print(f"❌ Error generating conceptual response with instructions: {e}")
            return ConceptualResponse(
                content=f"## Análisis Conceptual\n\nEstoy teniendo dificultades técnicas. Por favor, intenta nuevamente.\n\nError: {str(e)}",
                sources=[],
                confidence=0.1
            )

    async def _generate_accional_with_instructions(
        self, 
        message: str, 
        context: List[Dict],
        conceptual_content: str,
        instructions: List[Dict],
        ai_config: Any
    ) -> AccionalResponse:
        """
        Genera respuesta accional siguiendo instrucciones específicas
        """
        instruction_text = self._compile_instructions(instructions)
        
        system_prompt = f"""
        INSTRUCCIONES ESPECÍFICAS PARA PLANES DE ACCIÓN:
        {instruction_text}
        
        DEBES SEGUIR EXACTAMENTE ESTAS INSTRUCCIONES para generar planes de acción.
        
        Usa la metodología, estilo y estructura especificados en las instrucciones.
        
        Mantén respuestas concisas y accionables.
        """
        
        if len(conceptual_content) > 500:
            conceptual_content = conceptual_content[:500] + "..."
        
        prompt = f"""
        Basado en el siguiente análisis conceptual:
        {conceptual_content}
        
        Y la consulta original: "{message}"
        
        Siguiendo EXACTAMENTE las instrucciones proporcionadas:
        1. Genera el plan de acción según la metodología especificada
        2. Usa el formato y estructura indicados en las instrucciones
        3. Mantén el tono y estilo especificados
        4. Incluye los elementos requeridos por las instrucciones
        
        Respuesta CONCISA en Markdown siguiendo las instrucciones al pie de la letra.
        """
        
        model_name = ai_config.model_name if ai_config else settings.OPENAI_MODEL
        temperature = float(ai_config.temperature) if ai_config else 0.7
        max_tokens = (ai_config.max_tokens // 2) if ai_config else 700
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            content = response.choices[0].message.content
            
            # Determine priority and timeline from content
            priority = "media"
            if any(word in content.lower() for word in ["urgente", "inmediato", "crítico", "prioridad alta"]):
                priority = "alta"
            elif any(word in content.lower() for word in ["largo plazo", "eventualmente", "cuando sea posible"]):
                priority = "baja"
                
            timeline = "2-3 semanas"
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
            print(f"❌ Error generating accional response with instructions: {e}")
            return AccionalResponse(
                content=f"## Plan de Acción\n\nEstoy teniendo dificultades técnicas. Por favor, intenta nuevamente.\n\nError: {str(e)}",
                priority="media",
                timeline="Indefinido"
            )

    def _compile_knowledge(self, knowledge: List[Dict]) -> str:
        """
        Compila el conocimiento en un texto coherente
        """
        if not knowledge:
            return "No hay fuentes de conocimiento específicas configuradas."
        
        compiled = "FUENTES DE CONOCIMIENTO PRIORITARIAS:\n\n"
        
        for i, doc in enumerate(knowledge, 1):
            priority = doc.get('priority', 5)
            filename = doc.get('filename', f'documento_{i}')
            content = doc.get('content', '')[:2000]
            
            compiled += f"## FUENTE {i} (Prioridad {priority}) - {filename}\n"
            compiled += f"{content}\n\n"
        
        compiled += "\nUSA ESTAS FUENTES COMO REFERENCIA PRINCIPAL PARA TUS RESPUESTAS."
        return compiled

    def _build_enhanced_conversation_prompt(self, message: str, context: List[Dict], history: List[Dict], response_type: str, key_info: Dict[str, Any] = None) -> str:
        """
        Construye prompt mejorado para conversación con contexto priorizado
        """
        company_context = [ctx for ctx in context if ctx.get('category') == 'company_knowledge']
        general_context = [ctx for ctx in context if ctx.get('category') != 'company_knowledge']
        
        context_text = ""
        if company_context:
            context_text += "## CONTEXTO DE FUENTES DE CONOCIMIENTO PRIORITARIAS:\n"
            for i, doc in enumerate(company_context, 1):
                content = doc.get('content', '')[:1800]
                source = doc.get('source', 'documento')
                priority = doc.get('priority', 5)
                context_text += f"{i}. *{source}* (Prioridad {priority}):\n{content}\n\n"
        
        if general_context:
            context_text += "## CONTEXTO ADICIONAL (usar solo si es necesario):\n"
            for i, doc in enumerate(general_context, 1):
                content = doc.get('content', '')[:1000]
                source = doc.get('source', 'documento')
                context_text += f"{i}. *{source}*:\n{content}\n\n"
        
        history_text = ""
        if history and len(history) > 0:
            history_text = "## HISTORIAL COMPLETO DE CONVERSACIÓN:\n"
            recent_history = history[-10:] if len(history) > 10 else history
            for msg in recent_history:
                role_label = "Usuario" if msg.get("role") == "user" else "Asistente (tú)"
                content = msg.get("content", "")
                timestamp = msg.get("timestamp", "")
                history_text += f"*{role_label}* ({timestamp}): {content}\n\n"
            history_text += "---\n\n"
        
        key_info_text = ""
        if key_info:
            key_info_text = "## INFORMACIÓN CLAVE CONOCIDA:\n"
            if key_info.get("company_name"):
                key_info_text += f"- Empresa: {key_info['company_name']}\n"
            if key_info.get("industry"):
                key_info_text += f"- Industria: {key_info['industry']}\n"
            if key_info.get("objectives"):
                key_info_text += f"- Objetivos: {', '.join(key_info['objectives'])}\n"
            key_info_text += "\n"
        
        if response_type == "conceptual":
            prompt_specific = """
            GENERA UNA RESPUESTA CONCEPTUAL que:
            1. USE PRIORITARIAMENTE las fuentes de conocimiento específicas proporcionadas
            2. SIGA EXACTAMENTE las instrucciones configuradas
            3. RECUERDA toda la información previa de la conversación
            4. Explique el marco teórico basado en las fuentes prioritarias
            5. Solo use conocimiento general si las fuentes específicas no son suficientes
            
            CRÍTICO: Las fuentes de conocimiento prioritarias son tu referencia principal.
            """
        else:
            prompt_specific = """
            GENERA UN PLAN DE ACCIÓN que:
            1. USE las recomendaciones específicas de las fuentes de conocimiento prioritarias
            2. SIGA EXACTAMENTE las instrucciones configuradas para planes de acción
            3. CONSIDERE toda la información previa de la conversación
            4. Base las acciones en las fuentes prioritarias proporcionadas
            5. Solo complemente con conocimiento general si es necesario
            
            CRÍTICO: Las fuentes de conocimiento prioritarias definen tu metodología.
            """
        
        return f"""
        {key_info_text}
        {context_text}
        {history_text}
        
        {prompt_specific}
        
        Consulta actual: {message}
        """

    async def _generate_default_clarification(self, message: str) -> List[ClarificationQuestion]:
        """Genera preguntas de clarificación por defecto"""
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

    async def _generate_fallback_responses(self, message: str) -> Tuple[ConceptualResponse, AccionalResponse]:
        """Genera respuestas de fallback cuando hay errores"""
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

    def _parse_clarification_questions(self, content: str) -> List[ClarificationQuestion]:
        """Parsea la respuesta de OpenAI en objetos ClarificationQuestion"""
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

    def _count_tokens(self, text: str) -> int:
        """Cuenta tokens en un texto"""
        return len(self.encoding.encode(text))