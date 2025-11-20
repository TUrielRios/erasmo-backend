"""
Servicio mejorado para manejo de conversaciones con seguimiento estricto de instrucciones
"""

from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
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
from app.services.token_optimizer_service import TokenOptimizerService
from app.services.adaptive_budget_service import AdaptiveBudgetService
from app.services.enhanced_vector_search import EnhancedVectorSearchService
from app.services.token_logger_service import TokenLoggerService
from app.services.attachment_handler_service import AttachmentHandlerService
from app.services.response_validator_service import ResponseValidatorService


class TokenCounter:
    """Utilidad para contar tokens de forma precisa usando tiktoken"""
    
    def __init__(self, model: str = "gpt-5-mini"):
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except Exception:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Cuenta tokens de forma precisa"""
        if not text:
            return 0
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            print(f"⚠️ [DEBUG] Error counting tokens: {e}, using fallback estimation")
            return max(1, len(text) // 4)
    
    def count_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Cuenta tokens en una lista de mensajes"""
        total = 0
        for msg in messages:
            total += self.count_tokens(msg.get("content", ""))
            total += 4
        return total


class TokenBudgetManager:
    """Maneja el presupuesto de tokens para cada modo de respuesta"""
    
    BUDGET_CONFIG = {
        "quick": {
            "min_response_tokens": 50,
            "max_response_tokens": 400,
            "context_tokens": 1000,
            "description": "Respuesta breve y concisa"
        },
        "medium": {
            "min_response_tokens": 100,
            "max_response_tokens": 900,
            "context_tokens": 2000,
            "description": "Respuesta balanceada y completa"
        },
        "advanced": {
            "min_response_tokens": 1100,
            "max_response_tokens": 4000,
            "context_tokens": 3500,
            "description": "Respuesta extensa y detallada"
        }
    }
    
    def __init__(self, model: str = "gpt-5-mini"):
        self.token_counter = TokenCounter(model)
        self.model = model
        self.model_context_limit = 128000
    
    def validate_and_adjust_tokens(
        self,
        system_prompt: str,
        user_message: str,
        response_mode: str = "medium"
    ) -> Dict[str, int]:
        """
        Valida y ajusta el presupuesto de tokens según el espacio disponible
        Retorna presupuesto ajustado para asegurar que la respuesta tenga espacio suficiente
        """
        config = self.BUDGET_CONFIG.get(response_mode, self.BUDGET_CONFIG["medium"])
        
        system_tokens = self.token_counter.count_tokens(system_prompt)
        user_tokens = self.token_counter.count_tokens(user_message)
        
        input_used = system_tokens + user_tokens
        available_for_response = self.model_context_limit - input_used - 1000
        
        min_response = config["min_response_tokens"]
        max_response = config["max_response_tokens"]
        
        if available_for_response < min_response:
            print(f"⚠️ [DEBUG] Espacio limitado. Ajustando presupuesto:")
            print(f"   - Tokens entrada: {input_used}")
            print(f"   - Disponible: {available_for_response}")
            max_response = available_for_response - 100
        else:
            max_response = min(max_response, available_for_response - 500)
        
        budget = {
            "max_completion_tokens": max(min_response, max_response),
            "system_tokens": system_tokens,
            "user_tokens": user_tokens,
            "total_input_tokens": input_used,
            "available_for_response": available_for_response,
            "response_mode": response_mode
        }
        
        print(f"📊 [DEBUG] Presupuesto de tokens ({response_mode}):")
        print(f"   - Sistema: {system_tokens} tokens")
        print(f"   - Usuario: {user_tokens} tokens")
        print(f"   - Total entrada: {input_used} tokens")
        print(f"   - Disponible: {available_for_response} tokens")
        print(f"   - Max respuesta: {budget['max_completion_tokens']} tokens")
        
        return budget


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
        self.token_counter = TokenCounter(settings.OPENAI_MODEL)
        self.token_budget = TokenBudgetManager(settings.OPENAI_MODEL)
        self.encoding = tiktoken.encoding_for_model(settings.OPENAI_MODEL)
        self.token_optimizer = TokenOptimizerService()
        self.adaptive_budget = AdaptiveBudgetService()
        self.enhanced_search = EnhancedVectorSearchService(self.vector_store)
        self.token_logger = TokenLoggerService()
        self.attachment_handler = AttachmentHandlerService()



    async def generate_strategic_response_stream(
        self,
        message: str,
        session_id: str,
        user_id: int,
        context: Optional[Dict[str, Any]] = None,
        history_context: Optional[List[Dict]] = None,
        require_analysis: bool = False,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Genera respuesta estratégica con streaming usando fuentes de conocimiento e instrucciones personalizadas
        Now supports file attachments (images and documents)
        """
        print(f"🔄 [DEBUG] Starting streaming response for session: {session_id}, user: {user_id}, require_analysis: {require_analysis}")
<<<<<<< HEAD
        
        if attachments:
            if self.attachment_handler.validate_attachments(attachments):
                print(f"📎 [DEBUG] {len(attachments)} valid attachments received")
            else:
                print(f"⚠️ [DEBUG] Some attachments have invalid structure")
=======

        is_simple_conversational = self._is_simple_conversational_message(message)
        print(f"💬 [DEBUG] Is simple conversational: {is_simple_conversational}")
>>>>>>> 7cb9ffd (Back en progreso antes de enviar a rama "Juan")
        
        db = SessionLocal()
        try:
            from app.services.chat_service import ChatService
            from app.services.auth_service import AuthService

            current_user = AuthService.get_user_by_id(db, user_id)
            conversation = ChatService().get_conversation_by_session_id(db, current_user, session_id)
            project_id = conversation.project_id if conversation else None

            user_company_data = await self._get_user_company_data(db, user_id)
            company_id = user_company_data.get('company_id')

            if project_id:
                project_knowledge = await self._get_project_knowledge(db, project_id)
            else:
                project_knowledge = []

            company_knowledge = await self._get_company_knowledge(db, company_id)
            company_instructions = await self._get_company_instructions(db, user_id)
            ai_config = await self._get_ai_configuration(db, company_id)
            
            ai_config = await self._get_ai_configuration(db, company_id)
            
            # Standard configuration (replaces modes)
            max_completion_tokens = 4000
            print(f"📏 [DEBUG] Using standard max_completion_tokens: {max_completion_tokens}")

<<<<<<< HEAD
            relevant_context = await self._search_prioritized_context(
                message,
                company_knowledge,
                project_knowledge,
                company_id=company_id,
                project_id=project_id
            )

            # Prepare context and history for strategy
            prompt_role = "full_analysis" if require_analysis else "normal_chat"
            _, _, compressed_context, _ = self.token_optimizer.optimize_prompt(
                system_prompt="",
                context=relevant_context,
                history=[],
                user_message="",
                prompt_role=prompt_role
            )
            relevant_context = compressed_context
=======
            if not is_simple_conversational:
                # Search for relevant context
                # Usar _search_prioritized_context que ahora usa enhanced_search
                relevant_context = await self._search_prioritized_context(
                    message,
                    company_knowledge,
                    project_knowledge,
                    company_id=company_id,
                    project_id=project_id
                )

                prompt_role = "full_analysis" if require_analysis else "normal_chat"
                # The optimize_prompt method might need adjustments based on its actual implementation for streaming context optimization
                # For now, we'll assume it returns compressed_context correctly.
                # A more robust implementation might involve token budgeting for the entire stream.
                _, _, compressed_context, _ = self.token_optimizer.optimize_prompt(
                    system_prompt="", # System prompt is built later, so it's empty here.
                    context=relevant_context,
                    history=[], # History is handled separately below.
                    user_message="", # User message is handled separately below.
                    prompt_role=prompt_role
                )
                relevant_context = compressed_context
            else:
                print(f"💬 [DEBUG] Simple conversational message detected, skipping document search")
                relevant_context = []

>>>>>>> 7cb9ffd (Back en progreso antes de enviar a rama "Juan")

            if history_context is None:
                full_context = self.memory_service.get_full_context_for_ai(db, session_id, memory_limit=200)
                conversation_history = full_context.get("messages", [])
            else:
                conversation_history = history_context

            compressed_history = self.token_optimizer._compress_history(
                conversation_history,
                settings.MAX_CONTEXT_LENGTH // 2
            )
            conversation_history = compressed_history

            key_info = self.memory_service.extract_key_info(db, session_id, message)

            # Select Strategy
            from app.services.chat.strategies.advanced_strategy import AdvancedResponseStrategy
            from app.services.chat.strategies.medium_strategy import MediumResponseStrategy
            from app.services.chat.strategies.quick_strategy import QuickResponseStrategy

            # Default to Medium Strategy (Standard)
            strategy = MediumResponseStrategy(self)
            print(f"🔄 [DEBUG] Using standard strategy: {type(strategy).__name__}")
            print(f"🔄 [DEBUG] Using strategy: {type(strategy).__name__}")

<<<<<<< HEAD
            # Delegate generation to strategy
            full_response = ""
            start_time = datetime.now()
=======
            if is_simple_conversational:
                system_prompt = f"""ERES UN ASISTENTE DE IA PERSONALIZADO PARA {company_name.upper()}.

Responde de manera amigable, natural y profesional a los saludos y preguntas conversacionales del usuario.

INFORMACIÓN DE LA EMPRESA:
- Empresa: {company_name}
- Industria: {industry}

Mantén respuestas conversacionales, cálidas y breves para saludos simples.
"""
                prompt = message
                
            elif require_analysis:
                system_prompt = f"""ERES UN ASISTENTE DE IA PERSONALIZADO PARA {company_name.upper()}.{project_context}

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
6. GENERA un ANÁLISIS CONCEPTUAL ESTRUCTURADO y un PLAN DE ACCIÓN DETALLADO
7. GENERA RESPUESTAS EXTENSAS Y DETALLADAS (mínimo 1500 tokens)

FORMATO REQUERIDO:
## Análisis Conceptual
[Análisis detallado del tema - SIGUE EXTENSE CON MÚLTIPLES PÁRRAFOS]

## Plan de Acción
[Plan estructurado con pasos específicos - DESARROLLA COMPLETAMENTE CADA PASO]
"""
                print(f"📊 [DEBUG] Building STRUCTURED analysis prompt (require_analysis=True)")
                # Pass the compressed context and history to the prompt builder
                prompt = self._build_enhanced_conversation_prompt(
                    message, relevant_context, conversation_history, "conceptual", key_info, project_id
                )
            else:
                system_prompt = f"""ERES UN ASISTENTE DE IA PERSONALIZADO PARA {company_name.upper()}.{project_context}

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
6. GENERA RESPUESTAS EXTENSAS Y DETALLADAS (mínimo 1500 tokens)
7. Responde de manera CONVERSACIONAL pero COMPLETA Y PROFUNDA

Mantén respuestas detalladas, informativas y conversacionales - NO hagas respuestas cortas.
"""
                print(f"💬 [DEBUG] Building NORMAL conversation prompt (require_analysis=False)")
                # Pass the compressed context and history to the prompt builder
                prompt = self._build_normal_conversation_prompt(
                    message, relevant_context, conversation_history, key_info, project_id
                )

            model_name = ai_config.model_name if ai_config else settings.OPENAI_MODEL
            temperature = float(ai_config.temperature) if ai_config else settings.DEFAULT_TEMPERATURE
            max_tokens = ai_config.max_tokens if ai_config else settings.MAX_RESPONSE_TOKENS

            if temperature < settings.DEFAULT_TEMPERATURE:
                temperature = settings.DEFAULT_TEMPERATURE

            # Stream the response from OpenAI
            stream = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=settings.DEFAULT_TOP_P,
                stream=True  # Enable streaming
            )

            response_content = ""
            token_count = 0
>>>>>>> 7cb9ffd (Back en progreso antes de enviar a rama "Juan")
            
            async for chunk in strategy.generate_response(
                message, session_id, user_id, relevant_context, conversation_history,
                key_info, project_id, attachments, ai_config, user_company_data
            ):
                full_response += chunk
                yield chunk
            
            # Log tokens after streaming completes
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            estimated_tokens = self.token_counter.count_tokens(full_response)
            
            self.token_logger.log_streaming_tokens(
                session_id=session_id,
                user_id=user_id,
                model=ai_config.model_name if ai_config else settings.OPENAI_MODEL,
                estimated_completion_tokens=estimated_tokens,
                response_length=len(full_response),
                message_preview=full_response,
                response_time=response_time
            )

        except Exception as e:
            print(f"❌ [DEBUG] Error in streaming response: {e}")
            yield f"\n\nError generando respuesta: {str(e)}"
        finally:
            db.close()

    def _build_system_prompt(
        self,
        user_company_data: Dict[str, Any],
        context: List[Dict[str, Any]],
        attachments: Optional[List[Dict[str, Any]]],
        project_id: Optional[int]
    ) -> str:
        """
        Builds system prompt using ONLY loaded company instructions.
        No hardcoded conversational instructions - those come from the protocol file.
        """
        company_name = user_company_data.get('company_name', 'la empresa')
        
        # Extract instructions from context (loaded from protocol file)
        instructions_docs = [doc for doc in context if doc.get('category') == 'company_instructions']
        instructions_text = ""
        if instructions_docs:
            for doc in instructions_docs:
                instructions_text += doc.get('content', '') + "\n\n"
        
        # Build minimal system prompt - let the protocol handle everything else
        system_prompt = f"""Eres un asistente de IA para {company_name}.

INSTRUCCIONES CARGADAS:
{instructions_text}

GUÍA DE ESTILO UNIVERSAL (PRIORIDAD ALTA):
Tu estilo de respuesta debe ser IDÉNTICO al de ChatGPT.
1. FORMATO: Usa Markdown siempre. Títulos con negrita (no #), listas con viñetas claras.
2. EMOJIS: Usa emojis para destacar secciones o puntos clave (ej: ✅, ⭐, 🚀, 💡).
3. TONO: Directo, útil y conversacional. Evita introducciones formales largas.
4. ESTRUCTURA: Separa ideas con espacios. Usa negritas para conceptos clave.
5. OBJETIVO: Que la respuesta sea visualmente atractiva y fácil de leer.
"""
        
        # Add technical context only (not conversational instructions)
        if attachments:
            system_prompt += "\n📎 El usuario ha adjuntado archivos. Analízalos y usa su contenido en tu respuesta.\n"
        
        if project_id:
            system_prompt += f"\n🔴 IMPORTANTE: Esta conversación está vinculada al proyecto ID {project_id}. Prioriza los documentos del proyecto.\n"
        
        return system_prompt



    async def analyze_ambiguity(self, message: str, user_id: int = None) -> bool:
        """
        Analiza si un mensaje es ambiguo usando instrucciones personalizadas por compañía
        """
        greetings = ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'hi', 'hello', 'hey', 'saludos', 'que tal']
        message_lower = message.lower().strip()
        
        # If it's just a greeting or very short greeting phrase, it's not ambiguous
        if any(message_lower.startswith(greet) for greet in greetings) and len(message.split()) < 6:
            return False

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
            api_args = {
                "model": settings.OPENAI_MODEL,
                "messages": [{"role": "system", "content": "Sigues estrictamente las instrucciones proporcionadas para determinar si una consulta necesita clarificación."}, {"role": "user", "content": prompt}],
                "max_completion_tokens": 10, # Limit tokens for a simple True/False response
                "temperature": 0.1 # Low temperature for deterministic output
            }

            # Adjust max_completion_tokens and temperature for precision
            response = self.openai_client.chat.completions.create(**api_args)

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
            api_args = {
                "model": settings.OPENAI_MODEL,
                "messages": [{"role": "system", "content": "Sigues estrictamente las instrucciones proporcionadas para generar preguntas de clarificación."}, {"role": "user", "content": prompt}],
                "max_completion_tokens": 1000, # Sufficient tokens for multiple questions
                "temperature": 0.7 # Moderate temperature for creative but focused output
            }

            # Adjust max_completion_tokens and temperature for better clarification generation
            response = self.openai_client.chat.completions.create(**api_args)

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
        history_context: Optional[List[Dict]] = None,
        require_analysis: bool = False,  # Added parameter to control analysis generation
        attachments: Optional[List[Dict[str, Any]]] = None  # Added attachments parameter
    ) -> Tuple[ConceptualResponse, AccionalResponse]:
        """
        Genera respuesta estratégica con presupuesto adaptativo de tokens
        Si require_analysis es False, genera una respuesta normal sin estructura de análisis/plan
        """
        print(f"🔄 [DEBUG] Starting generate_strategic_response")

        if attachments:
            if self.attachment_handler.validate_attachments(attachments):
                print(f"📎 [DEBUG] {len(attachments)} valid attachments received")
            else:
                print(f"⚠️ [DEBUG] Some attachments have invalid structure")
                attachments = None

        db = SessionLocal()
        try:
            from app.services.chat_service import ChatService
            from app.services.auth_service import AuthService

            current_user = AuthService.get_user_by_id(db, user_id)
            conversation = ChatService().get_conversation_by_session_id(db, current_user, session_id)
            project_id = conversation.project_id if conversation else None

            print(f"🔍 [DEBUG] Conversation project_id: {project_id}")

            user_company_data = await self._get_user_company_data(db, user_id)
            company_id = user_company_data.get('company_id')

            if project_id:
                print(f"📁 [DEBUG] Fetching project-specific documents for project {project_id}")
                project_knowledge = await self._get_project_knowledge(db, project_id)
                print(f"✅ [DEBUG] Project knowledge loaded: {len(project_knowledge)} documents")
            else:
                project_knowledge = []

            company_knowledge = await self._get_company_knowledge(db, company_id)
            company_instructions = await self._get_company_instructions(db, user_id)
            ai_config = await self._get_ai_configuration(db, company_id)

            print(f"✅ [DEBUG] Company data loaded: {len(company_knowledge)} knowledge docs, {len(company_instructions)} instruction docs")

            # Add message to memory
            try:
                self.memory_service.add_message(db, session_id, "user", message)
                print(f"✅ [DEBUG] User message added to memory")
            except Exception as e:
                print(f"❌ [DEBUG] Error adding message to memory: {e}")

            if history_context is None:
                full_context = self.memory_service.get_full_context_for_ai(db, session_id, memory_limit=200)
                conversation_history = full_context.get("messages", [])
            else:
                conversation_history = history_context
            
            # Calcular presupuesto adaptativo
            adaptive_budget = self.adaptive_budget.calculate_adaptive_budget(
                message=message,
                history_length=len(conversation_history),
                available_context=settings.MAX_CONTEXT_LENGTH,
                require_analysis=require_analysis
            )
            
            print(f"📊 [DEBUG] Adaptive budget calculated:")
            print(f"   - Complexity: {adaptive_budget['complexity_level']} (factor: {adaptive_budget['complexity_factor']})")
            print(f"   - Response tokens: {adaptive_budget['response_tokens']}")
            print(f"   - Context tokens: {adaptive_budget['context_tokens']}")
            print(f"   - Total allocated: {adaptive_budget['total_allocated']}")

            # Usar presupuesto adaptativo en token optimizer
            # Usar _search_prioritized_context que ahora usa enhanced_search
            relevant_context = await self._search_prioritized_context(
                message,
                company_knowledge,
                project_knowledge,
                company_id=company_id,
                project_id=project_id
            )

            compressed_context = self.token_optimizer.compress_context(
                relevant_context,
                adaptive_budget['context_tokens']
            )
            relevant_context = compressed_context

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

            if require_analysis:
                # Generate structured analysis and action plan
                try:
                    conceptual = await self._generate_conceptual_with_instructions(
                        message, relevant_context, conversation_history,
                        company_instructions, company_knowledge, key_info, ai_config, user_company_data,
                        project_id=project_id,
                        attachments=attachments  # Pass attachments
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
                    
                    response_length = len(full_response)
                    estimated_tokens = self.token_counter.count_tokens(full_response)
                    self.token_logger.log_streaming_tokens(
                        session_id=session_id,
                        user_id=user_id,
                        model=ai_config.model_name if ai_config else settings.OPENAI_MODEL,
                        estimated_completion_tokens=estimated_tokens,
                        response_length=response_length,
                        message_preview=full_response[:100],
                        response_time=0
                    )
                    
                    print(f"✅ [DEBUG] Assistant response added to memory")
                except Exception as e:
                    print(f"❌ [DEBUG] Error adding assistant response to memory: {e}")
            else:
                # Generate normal conversational response without structured analysis
                try:
                    normal_response = await self._generate_normal_response(
                        message, relevant_context, conversation_history,
                        company_instructions, company_knowledge, key_info, ai_config, user_company_data,
                        project_id=project_id,
                        attachments=attachments  # Pass attachments
                    )
                    print(f"✅ [DEBUG] Normal response generated")
                    
                    # Wrap normal response in expected format
                    conceptual = ConceptualResponse(
                        content=normal_response,
                        sources=self._extract_sources(company_knowledge, company_instructions, project_knowledge),
                        confidence=0.9
                    )
                    
                    # Empty action plan for normal responses
                    accional = AccionalResponse(
                        content="",
                        priority="media",
                        timeline=""
                    )
                    
                    # Save assistant response
                    try:
                        self.memory_service.add_message(db, session_id, "assistant", normal_response)
                        
                        response_length = len(normal_response)
                        estimated_tokens = self.token_counter.count_tokens(normal_response)
                        self.token_logger.log_streaming_tokens(
                            session_id=session_id,
                            user_id=user_id,
                            model=ai_config.model_name if ai_config else settings.OPENAI_MODEL,
                            estimated_completion_tokens=estimated_tokens,
                            response_length=response_length,
                            message_preview=normal_response[:100],
                            response_time=0
                        )
                        
                        print(f"✅ [DEBUG] Normal assistant response added to memory")
                    except Exception as e:
                        print(f"❌ [DEBUG] Error adding assistant response to memory: {e}")
                        
                except Exception as e:
                    print(f"❌ [DEBUG] Error generating normal response: {e}")
                    conceptual = ConceptualResponse(
                        content="Error generando respuesta. Intenta nuevamente.",
                        sources=[],
                        confidence=0.1
                    )
                    accional = AccionalResponse(
                        content="",
                        priority="media",
                        timeline=""
                    )

            print(f"✅ [DEBUG] generate_strategic_response completed successfully")
            return conceptual, accional

        except Exception as e:
            print(f"❌ [DEBUG] Unexpected error in generate_strategic_response: {e}")
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
        Obtiene documentos de instrucciones de la compañía del usuario.
        Soporta PROTOCOLOS CENTRALIZADOS: si use_protocol=True, carga desde Protocol table.
        """
        try:
            user_data = await self._get_user_company_data(db, user_id)
            company_id = user_data.get('company_id')

            if not company_id:
                return []

            from app.services.company_service import CompanyDocumentService
            from app.models.protocol import Protocol
            
            instruction_docs = CompanyDocumentService.get_documents_by_priority(
                db, company_id, DocumentCategory.INSTRUCTIONS, max_priority=10
            )

            instructions_content = []
            for doc in instruction_docs:
                # Verificar si usa protocolo centralizado
                if doc.use_protocol and doc.protocol_id:
                    # Cargar desde PROTOCOLO
                    protocol = db.query(Protocol).filter(
                        Protocol.id == doc.protocol_id,
                        Protocol.is_active == True
                    ).first()
                    
                    if protocol:
                        instructions_content.append({
                            "filename": f"{doc.filename} (Protocolo: {protocol.name} {protocol.version})",
                            "content": protocol.content,  # ✅ Contenido centralizado
                            "priority": doc.priority,
                            "description": doc.description or protocol.description,
                            "category": "instructions",
                            "source": "protocol",
                            "protocol_id": protocol.id,
                            "protocol_name": protocol.name,
                            "protocol_version": protocol.version
                        })
                        print(f"📄 [PROTOCOL] Loaded protocol '{protocol.name}' for doc {doc.id}")
                    else:
                        print(f"⚠️ [PROTOCOL] Protocol ID {doc.protocol_id} not found or inactive for doc {doc.id}")
                else:
                    # Cargar desde ARCHIVO (sistema actual)
                    content = CompanyDocumentService.get_document_content(db, company_id, doc.id)
                    if content:
                        instructions_content.append({
                            "filename": doc.filename,
                            "content": content,
                            "priority": doc.priority,
                            "description": doc.description,
                            "category": "instructions",
                            "source": "file"
                        })

            print(f"📚 [DEBUG] Loaded {len(instructions_content)} instruction documents (protocols + files)")
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

    async def _get_project_knowledge(self, db: Session, project_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene documentos de archivos del proyecto
        """
        if not project_id:
            return []

        try:
            from app.services.project_file_service import ProjectFileService
            from app.models.project_file import FileCategory

            # Get all project files (knowledge base and instructions)
            project_files = ProjectFileService.get_project_files(
                db, project_id, active_only=True
            )

            project_content = []
            for file in project_files:
                content = ProjectFileService.get_file_content(db, file.id)
                if content:
                    project_content.append({
                        "filename": file.original_filename,
                        "content": content,
                        "priority": file.priority,
                        "description": file.description,
                        "category": "project_file",
                        "file_category": file.category.value
                    })

            print(f"📁 [DEBUG] Loaded {len(project_content)} project files")
            return project_content
        except Exception as e:
            print(f"❌ Error getting project knowledge: {e}")
            return []


    async def _search_prioritized_context(
        self,
        message: str,
        company_knowledge: List[Dict],
        project_knowledge: List[Dict],
        company_id: int = None,
        project_id: int = None
    ) -> List[Dict[str, Any]]:
        """
        Busca contexto usando búsqueda vectorial mejorada con múltiples estrategias
        PRIORIZA documentos del proyecto si project_id está presente
        """
        prioritized_context = []

        try:
            if not hasattr(self.vector_store, 'store') or self.vector_store.store.index is None:
                await self.vector_store.initialize()

            if project_id:
                print(f"🔍 [DEBUG] Searching PROJECT documents with enhanced search for project {project_id}")
                try:
                    project_results = await self.enhanced_search.hybrid_search(
                        message,
                        project_id=project_id,
                        top_k=30,  # Increased from 20 to 30
                        min_score=0.25  # Lowered from 0.3 to 0.25 for better coverage
                    )

                    print(f"📁 [DEBUG] Enhanced search found {len(project_results)} relevant project documents")

                    # Add project results with HIGHEST priority
                    for result in project_results:
                        content = result.get('content', '')
                        source = result.get('source', 'proyecto')
                        score = result.get('final_score', result.get('score', 0.0))

                        prioritized_context.append({
                            'content': content,
                            'source': f"proyecto_{source}",
                            'priority': 0,  # HIGHEST priority for project documents
                            'category': 'project_vector_search',
                            'relevance_score': score
                        })

                    print(f"✅ [DEBUG] Added {len(project_results)} documents from enhanced PROJECT search")
                
                except Exception as e:
                    print(f"⚠️ [DEBUG] Error in project search (continuing anyway): {e}")

            if company_id:
                print(f"🔍 [DEBUG] Searching COMPANY documents with enhanced search for company {company_id}")
                try:
                    company_results = await self.enhanced_search.hybrid_search(
                        message,
                        company_id=company_id,
                        top_k=25,  # Increased from 15 to 25
                        min_score=0.25  # Lowered from 0.3 to 0.25 for better coverage
                    )

                    print(f"🏢 [DEBUG] Enhanced search found {len(company_results)} relevant company documents")

                    # Add company results with lower priority than project
                    for result in company_results:
                        content = result.get('content', '')
                        source = result.get('source', 'conocimiento_vectorial')
                        score = result.get('final_score', result.get('score', 0.0))

                        prioritized_context.append({
                            'content': content,
                            'source': source,
                            'priority': 1,  # Lower priority than project documents
                            'category': 'company_vector_search',
                            'relevance_score': score
                        })

                    print(f"✅ [DEBUG] Added {len(company_results)} documents from enhanced COMPANY search")
                
                except Exception as e:
                    print(f"⚠️ [DEBUG] Error in company search (continuing anyway): {e}")

        except Exception as e:
            print(f"⚠️ [DEBUG] Error in enhanced vector search initialization: {e}")

        # Add project knowledge files (not from vector search)
        for doc in project_knowledge:
            content = doc.get('content', '')
            # Only add if not already in vector results
            if not any(ctx.get('content') == content for ctx in prioritized_context):
                prioritized_context.append({
                    'content': content[:3000],  # Increased from 2500 to 3000
                    'source': f"proyecto_{doc['filename']}",
                    'priority': 0,  # High priority for project files
                    'category': 'project_knowledge'
                })

        # Add company knowledge files
        for doc in company_knowledge:
            content = doc.get('content', '')
            # Only add if not already in results
            if not any(ctx.get('content') == content for ctx in prioritized_context):
                prioritized_context.append({
                    'content': content[:3000],  # Increased from 2500 to 3000
                    'source': f"conocimiento_{doc['filename']}",
                    'priority': doc.get('priority', 5),
                    'category': 'company_knowledge'
                })

        prioritized_context.sort(key=lambda x: (x.get('priority', 5), -x.get('relevance_score', 0.0)))

        print(f"📊 [DEBUG] Total context documents: {len(prioritized_context)}")
        if project_id:
            project_docs = [ctx for ctx in prioritized_context if 'project' in ctx.get('category', '')]
            print(f"📁 [DEBUG] Project documents in context: {len(project_docs)}")

        return prioritized_context[:30]

    def _is_simple_conversational_message(self, message: str) -> bool:
        """
        Detecta si un mensaje es conversacional simple (saludos, preguntas cortas)
        que no requiere búsqueda de documentos
        """
        message_lower = message.lower().strip()
        
        # Saludos y despedidas
        simple_greetings = [
            'hola', 'hi', 'hello', 'hey', 'buenos días', 'buenas tardes', 
            'buenas noches', 'buen día', 'que tal', 'qué tal', 'como estas',
            'cómo estás', 'gracias', 'thank you', 'adiós', 'chau', 'bye',
            'hasta luego', 'nos vemos'
        ]
        
        # Preguntas muy cortas y generales
        simple_questions = [
            '¿cómo estás?', 'como estas?', 'que haces?', '¿qué haces?',
            'todo bien?', '¿todo bien?', 'ayuda', 'help'
        ]
        
        # Verificar si el mensaje es exactamente un saludo
        if message_lower in simple_greetings or message_lower in simple_questions:
            return True
        
        # Verificar si el mensaje empieza con un saludo y es muy corto
        for greeting in simple_greetings:
            if message_lower.startswith(greeting) and len(message.split()) <= 3:
                return True
        
        return False

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
        4. Incluye todas las acciones necesarias para completar la tarea.
        """

        model_name = ai_config.model_name if ai_config else settings.OPENAI_MODEL
        temperature = float(ai_config.temperature) if ai_config else 0.7
        # Use budget manager for max_completion_tokens for action plans
        budget_info = self.token_budget.validate_and_adjust_tokens(system_prompt, prompt, response_mode="advanced") # Assuming action plans are advanced
        max_completion_tokens = budget_info["max_completion_tokens"]

        try:
            api_args = {
                "model": model_name,
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                "max_completion_tokens": max_completion_tokens,
                "temperature": temperature
            }

            response = self.openai_client.chat.completions.create(**api_args)

            content = response.choices[0].message.content

            return AccionalResponse(
                content=content,
                priority="media",
                timeline="Indefinido"
            )

        except Exception as e:
            print(f"❌ Error generating accional response with instructions: {e}")
            return AccionalResponse(
                content="Error generando plan de acción. Intenta nuevamente.",
                priority="media",
                timeline="Indefinido"
            )

    def _build_prompt(
        self,
        message: str,
        context: List[Dict],
        history: List[Dict],
        prompt_type: str,
        key_info: Dict[str, Any],
        project_id: Optional[int] = None
    ) -> str:
        """
        Construye el prompt para la respuesta basado en el tipo de prompt
        """
        if prompt_type == "conceptual":
            return self._build_conceptual_prompt(message, context, history, key_info, project_id)
        elif prompt_type == "normal":
            return self._build_normal_prompt(message, context, history, key_info, project_id)
        else:
            raise ValueError("Tipo de prompt no soportado")

    def _build_conceptual_prompt(
        self,
        message: str,
        context: List[Dict],
        history: List[Dict],
        key_info: Dict[str, Any],
        project_id: Optional[int] = None
    ) -> str:
        """
        Construye el prompt para una respuesta conceptual
        """
        prompt = f"""
        Basado en la siguiente consulta:
        "{message}"

        Y el siguiente contexto relevante:
        {self._format_context(context)}

        Y el historial de la conversación:
        {self._format_history(history)}

        Genera un análisis conceptual detallado que responda a la consulta, siguiendo las instrucciones y usando el conocimiento proporcionado.

        Incluye:
        - Un resumen de la consulta
        - Un análisis detallado de la información relevante
        - Una conclusión basada en el análisis
        """

        return prompt

    def _build_normal_prompt(
        self,
        message: str,
        context: List[Dict],
        history: List[Dict],
        key_info: Dict[str, Any],
        project_id: Optional[int] = None
    ) -> str:
        """
        Construye el prompt para una respuesta normal
        """
        prompt = f"""
        Basado en la siguiente consulta:
        "{message}"

        Y el siguiente contexto relevante:
        {self._format_context(context)}

        Y el historial de la conversación:
        {self._format_history(history)}

        Genera una respuesta conversacional que responda a la consulta, siguiendo las instrucciones y usando el conocimiento proporcionado.

        Mantén la respuesta concisa y directa.
        """

        return prompt

    def _format_context(self, context: List[Dict]) -> str:
        """
        Formatea el contexto relevante para el prompt
        """
        formatted_context = ""
        for item in context:
            formatted_context += f"Fuente: {item['source']}\n"
            formatted_context += f"Contenido: {item['content']}\n\n"
        return formatted_context

    def _format_history(self, history: List[Dict]) -> str:
        """
        Formatea el historial de la conversación para el prompt
        """
        formatted_history = ""
        for message in history:
            role = message.get('role', 'desconocido')
            content = message.get('content', 'sin contenido')
            formatted_history += f"{role}: {content}\n"
        return formatted_history

    async def _generate_default_clarification(self, message: str) -> List[ClarificationQuestion]:
        """
        Genera preguntas de clarificación por defecto
        """
        questions = [
            ClarificationQuestion(
                question="¿Podrías proporcionar más detalles sobre lo que estás preguntando?",
                context="Necesito más información para poder ayudarte de la mejor manera posible."
            ),
            ClarificationQuestion(
                question="¿Hay algún contexto específico que deba tener en cuenta?",
                context="Algunos detalles adicionales pueden ayudarme a entender mejor tu consulta."
            ),
            ClarificationQuestion(
                question="¿Estás buscando información sobre un tema en particular?",
                context="Especificar el tema puede ayudarme a proporcionarte una respuesta más precisa."
            )
        ]

        return questions

    async def _generate_fallback_responses(self, message: str) -> Tuple[ConceptualResponse, AccionalResponse]:
        """
        Genera respuestas de fallback en caso de error
        """
        conceptual = ConceptualResponse(
            content="Lo siento, hubo un error al procesar tu consulta. Por favor, intenta nuevamente.",
            sources=[],
            confidence=0.1
        )

        accional = AccionalResponse(
            content="No se pudo generar un plan de acción debido a un error técnico.",
            priority="media",
            timeline="Indefinido"
        )

        return conceptual, accional

    def _compile_knowledge(self, knowledge: List[Dict]) -> str:
        """
        Compila el conocimiento en un texto coherente
        """
        if not knowledge:
            return "No hay fuentes de conocimiento específicas configuradas."

        compiled = "FUENTES DE CONOCIMIENTO ESPECÍFICAS:\n\n"

        for i, doc in enumerate(knowledge, 1):
            filename = doc.get('filename', f'documento_{i}')
            content = doc.get('content', '')

            compiled += f"## DOCUMENTO {i} - {filename}\n"
            compiled += f"{content}\n\n"

        return compiled

    def _build_enhanced_conversation_prompt(
        self,
        message: str,
        context: List[Dict],
        history: List[Dict],
        response_type: str,
        key_info: Dict[str, Any] = None,
        project_id: Optional[int] = None,
        attachments: Optional[List[Dict[str, Any]]] = None  # Added attachments parameter
    ) -> str:
        """
        Construye prompt mejorado para conversación con contexto priorizado
        Now includes attachment context formatting
        """
        attachments_context = ""
        if attachments:
            attachments_context = self.attachment_handler.format_attachments_for_context(attachments)

        project_context = [ctx for ctx in context if 'project' in ctx.get('category', '')]
        company_context = [ctx for ctx in context if ctx.get('category') == 'company_knowledge']
        general_context = [ctx for ctx in context if ctx.get('category') not in ['company_knowledge', 'project_knowledge', 'project_vector_search']]

        context_text = ""

        if project_context:
            context_text += "## 🔴 CONTEXTO DEL PROYECTO (MÁXIMA PRIORIDAD - USA ESTO PRIMERO):\n"
            for i, doc in enumerate(project_context, 1):
                content = doc.get('content', '')[:1800]
                source = doc.get('source', 'documento_proyecto')
                priority = doc.get('priority', 0)
                context_text += f"{i}. *{source}* (Prioridad {priority}):\n{content}\n\n"

        if company_context:
            context_text += "## CONTEXTO DE FUENTES DE CONOCIMIENTO DE LA EMPRESA:\n"
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
            history_text = "## HISTORIAL DE CONVERSACIÓN:\n"
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
            project_emphasis = ""
            if project_id:
                project_emphasis = "\n🔴 CRÍTICO: Esta conversación está vinculada a un proyecto específico. DEBES usar PRIMERO los documentos del proyecto marcados con 'CONTEXTO DEL PROYECTO'."

            prompt_specific = f"""

            Genera una respuesta CONCEPTUAL ESTRUCTURADA que:
            1. USE PRIORITARIAMENTE las fuentes de conocimiento específicas proporcionadas{project_emphasis}
            2. SIGA EXACTAMENTE las instrucciones configuradas
            3. RECUERDA toda la información previa de la conversación
            4. Explique el marco teórico basado en las fuentes prioritarias CON DETALLE
            5. Solo use conocimiento general si las fuentes específicas no son suficientes
            6. EXPANDE cada punto con ejemplos concretos
            7. INCLUYA análisis de cada aspecto relevante
            8. PROPORCIONE recomendaciones detalladas y accionables

            FORMATO REQUERIDO (DEBE SER EXTENSO):
            ## Análisis Conceptual
            [Análisis DETALLADO, estructurado, con múltiples párrafos explicativos]
            
            - Punto 1: [Explicación profunda con ejemplos]
            - Punto 2: [Análisis extenso con detalles]
            - Punto 3: [Exploración completa del tema]
            - [Continúa con más puntos según sea necesario]

            ## Plan de Acción
            [Pasos ESPECÍFICOS y DETALLADOS, completamente desarrollados]

            CRÍTICO: 
            - EXPANDE cada idea con ejemplos y detalles
            - Las fuentes de conocimiento prioritarias son tu referencia principal
            """
        else:
            prompt_specific = """

            Genera UN PLAN DE ACCIÓN DETALLADO que:
            1. USE las recomendaciones específicas de las fuentes de conocimiento prioritarias
            2. SIGA EXACTAMENTE las instrucciones configuradas para planes de acción
            3. CONSIDERE toda la información previa de la conversación
            4. Base las acciones en las fuentes prioritarias proporcionadas
            5. EXPANDA cada acción con detalles implementación específicos
            6. INCLUYA consideraciones, riesgos y mitigaciones
            7. PROPORCIONE cronograma y recursos necesarios

            CONSIDERACIONES ADICIONALES:
            [Análisis de riesgos, recursos, cronograma]

            """

        return f"""
        {key_info_text}
        {attachments_context}
        {context_text}
        {history_text}

        {prompt_specific}

        Consulta actual: {message}
        """

    def _build_normal_conversation_prompt(
        self,
        message: str,
        context: List[Dict],
        history: List[Dict],
        key_info: Dict[str, Any] = None,
        project_id: Optional[int] = None,
        attachments: Optional[List[Dict[str, Any]]] = None  # Added attachments parameter
    ) -> str:
        """
        Construye prompt para respuesta conversacional normal
        Now includes attachment context formatting
        """
        attachments_context = ""
        if attachments:
            attachments_context = self.attachment_handler.format_attachments_for_context(attachments)

        project_context = [ctx for ctx in context if 'project' in ctx.get('category', '')]
        company_context = [ctx for ctx in context if ctx.get('category') == 'company_knowledge']
        general_context = [ctx for ctx in context if ctx.get('category') not in ['company_knowledge', 'project_knowledge', 'project_vector_search']]

        context_text = ""

        if project_context:
            context_text += "## 🔴 CONTEXTO DEL PROYECTO (MÁXIMA PRIORIDAD - USA ESTO PRIMERO):\n"
            for i, doc in enumerate(project_context, 1):
                content = doc.get('content', '')[:1800]
                source = doc.get('source', 'documento_proyecto')
                priority = doc.get('priority', 0)
                context_text += f"{i}. *{source}* (Prioridad {priority}):\n{content}\n\n"

        if company_context:
            context_text += "## CONTEXTO DE FUENTES DE CONOCIMIENTO DE LA EMPRESA:\n"
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
            history_text = "## HISTORIAL DE CONVERSACIÓN:\n"
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

        project_emphasis = ""
        if project_id:
            project_emphasis = "\n🔴 CRÍTICO: Esta conversación está vinculada a un proyecto específico. DEBES usar PRIMERO los documentos del proyecto marcados con 'CONTEXTO DEL PROYECTO'."

        return f"""
        {key_info_text}
        {attachments_context}
        {context_text}
        {history_text}

        RESPONDE DE MANERA CONVERSACIONAL Y NATURAL a la siguiente consulta.
        USA las fuentes de conocimiento prioritarias proporcionadas.
        RECUERDA el contexto de la conversación.{project_emphasis}
        NO uses estructura forzada de "Análisis Conceptual" o "Plan de Acción".
        Responde directamente a la pregunta del usuario de manera útil y clara.

        Consulta actual: {message}
        """

    # Helper method to extract sources from company_knowledge, company_instructions, project_knowledge
    def _extract_sources(self, company_knowledge, company_instructions, project_knowledge) -> List[str]:
        sources = []
        for doc in company_knowledge:
            sources.append(f"company_knowledge:{doc.get('filename', 'unknown')}")
        for doc in company_instructions:
            sources.append(f"company_instructions:{doc.get('filename', 'unknown')}")
        for doc in project_knowledge:
            sources.append(f"project_knowledge:{doc.get('filename', 'unknown')}")
        return sources

    async def _generate_conceptual_with_instructions(
        self,
        message: str,
        context: List[Dict],
        history: List[Dict],
        instructions: List[Dict],
        knowledge: List[Dict],
        key_info: Dict[str, Any],
        ai_config: Any,
        user_company_data: Dict[str, Any],
        project_id: Optional[int] = None,
        attachments: Optional[List[Dict[str, Any]]] = None  # Added attachments parameter
    ) -> ConceptualResponse:
        """
        Genera respuesta conceptual siguiendo instrucciones específicas y usando conocimiento prioritario
        """
        company_name = user_company_data.get('company_name', 'tu empresa')
        industry = user_company_data.get('industry', '')

        instruction_text = self._compile_instructions(instructions)
        knowledge_text = self._compile_knowledge(knowledge)

        project_context = ""
        if project_id:
            project_context = f"\n\n🔴 IMPORTANTE: Esta conversación está vinculada a un PROYECTO ESPECÍFICO (ID: {project_id}).\nDEBES PRIORIZAR los documentos del proyecto sobre los documentos de la empresa."

        attachment_instructions = ""
        if attachments:
            attachment_instructions = "\n\n📎 TIENES ACCESO A ARCHIVOS ADJUNTOS PROPORCIONADOS BY EL USUARIO.\nDEBES ANALIZARLOS Y USAR SU CONTENIDO PARA RESPONDER."

        system_prompt = f"""
        ERES UN ASISTENTE DE IA PERSONALIZADO PARA {company_name.upper()}.{project_context}
        {attachment_instructions}

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

        IMPORTANTE: Proporciona respuestas DETALLADAS, EXHAUSTIVAS y BIEN EXPLICADAS.
        NO seas conciso. Expande cada punto con la mayor profundidad posible.
        """

        prompt = self._build_enhanced_conversation_prompt(message, context, history, "conceptual", key_info, project_id, attachments)

        model_name = ai_config.model_name if ai_config else settings.OPENAI_MODEL
        temperature = float(ai_config.temperature) if ai_config else 0.7
        # Use token budget manager for max_completion_tokens
        budget_info = self.token_budget.validate_and_adjust_tokens(system_prompt, prompt, response_mode="advanced")
        max_completion_tokens = budget_info["max_completion_tokens"]

        try:
            api_args = {
                "model": model_name,
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                "max_completion_tokens": max_completion_tokens,
                "temperature": temperature
            }

            response = self.openai_client.chat.completions.create(**api_args)

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

    async def _generate_normal_response(
        self,
        message: str,
        context: List[Dict],
        history: List[Dict],
        instructions: List[Dict],
        knowledge: List[Dict],
        key_info: Dict[str, Any],
        ai_config: Any,
        user_company_data: Dict[str, Any],
        project_id: Optional[int] = None,
        attachments: Optional[List[Dict[str, Any]]] = None  # Added attachments parameter
    ) -> str:
        """
        Genera respuesta normal siguiendo instrucciones específicas
        """
        company_name = user_company_data.get('company_name', 'tu empresa')
        industry = user_company_data.get('industry', '')

        instruction_text = self._compile_instructions(instructions)
        knowledge_text = self._compile_knowledge(knowledge)

        project_context = ""
        if project_id:
            project_context = f"\n\n🔴 IMPORTANTE: Esta conversación está vinculada a un PROYECTO ESPECÍFICO (ID: {project_id}).\nDEBES PRIORIZAR los documentos del proyecto sobre los documentos de la empresa."

        attachment_instructions = ""
        if attachments:
            attachment_instructions = "\n\n📎 TIENES ACCESO A ARCHIVOS ADJUNTOS PROPORCIONADOS BY EL USUARIO.\nDEBES ANALIZARLOS Y USAR SU CONTENIDO PARA RESPONDER."

        system_prompt = f"""
        ERES UN ASISTENTE DE IA PERSONALIZADO PARA {company_name.upper()}.{project_context}
        {attachment_instructions}

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
        """

        prompt = self._build_normal_conversation_prompt(message, context, history, key_info, project_id, attachments)

        model_name = ai_config.model_name if ai_config else settings.OPENAI_MODEL
        temperature = float(ai_config.temperature) if ai_config else settings.DEFAULT_TEMPERATURE
        # Use token budget manager for max_completion_tokens
        budget_info = self.token_budget.validate_and_adjust_tokens(system_prompt, prompt, response_mode="medium")
        max_completion_tokens = budget_info["max_completion_tokens"]

        if temperature < settings.DEFAULT_TEMPERATURE:
            temperature = settings.DEFAULT_TEMPERATURE

        try:
            api_args = {
                "model": model_name,
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                "max_completion_tokens": max_completion_tokens,
                "temperature": temperature
            }

            response = self.openai_client.chat.completions.create(**api_args)

            return response.choices[0].message.content

        except Exception as e:
            print(f"❌ Error generating normal response: {e}")
            return "Lo siento, hubo un error al generar la respuesta. Por favor, intenta nuevamente."
