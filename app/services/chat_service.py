"""
Servicio optimizado para gestión de sesiones de chat con conciencia de contexto avanzada
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from datetime import datetime, timedelta
import uuid

from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.schemas import ConversationCreate, ConversationResponse, ConversationWithMessages, MessageResponse
from app.services.memory_service import MemoryService

class ChatService:
    """Servicio optimizado para gestión de chats con conciencia de contexto avanzada"""
    
    def __init__(self):
        self.memory_service = MemoryService()
    
    def create_conversation(
        self, 
        db: Session, 
        user: User, 
        conversation_data: ConversationCreate
    ) -> Conversation:
        """Crear nueva conversación para un usuario"""
        
        # Generar session_id único
        session_id = str(uuid.uuid4())
        
        # Crear título automático si no se proporciona
        title = conversation_data.title
        if not title:
            title = f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        # Crear conversación con o sin proyecto
        db_conversation = Conversation(
            session_id=session_id,
            user_id=user.id,
            project_id=conversation_data.project_id,  # Puede ser None
            title=title,
            is_active=True
        )
        
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        
        return db_conversation
    
    def get_user_conversations(
        self, 
        db: Session, 
        user: User, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[ConversationResponse]:
        """Obtener todas las conversaciones de un usuario"""
        
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user.id,
            Conversation.is_active == True
        ).order_by(desc(Conversation.updated_at)).offset(skip).limit(limit).all()
        
        # Convertir a response con conteo de mensajes
        result = []
        for conv in conversations:
            message_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
            
            conv_response = ConversationResponse(
                id=conv.id,
                session_id=conv.session_id,
                user_id=conv.user_id,
                project_id=conv.project_id,  # Incluir project_id en la respuesta
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                is_active=conv.is_active,
                message_count=message_count
            )
            result.append(conv_response)
        
        return result
    
    def get_conversation_by_session_id(
        self, 
        db: Session, 
        user: User, 
        session_id: str
    ) -> Optional[Conversation]:
        """Obtener conversación por session_id verificando que pertenezca al usuario"""
        
        return db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.user_id == user.id,
            Conversation.is_active == True
        ).first()
    
    def get_conversation_with_messages(
        self, 
        db: Session, 
        user: User, 
        session_id: str,
        message_limit: int = 100
    ) -> Optional[ConversationWithMessages]:
        """Obtener conversación completa con sus mensajes"""
        
        conversation = self.get_conversation_by_session_id(db, user, session_id)
        if not conversation:
            return None
        
        # Obtener mensajes de la conversación
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.timestamp).limit(message_limit).all()
        
        # Convertir mensajes a response
        message_responses = [
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                message_metadata=msg.message_metadata
            ) for msg in messages
        ]
        
        # Crear response completo
        return ConversationWithMessages(
            id=conversation.id,
            session_id=conversation.session_id,
            user_id=conversation.user_id,
            project_id=conversation.project_id,  # Incluir project_id en la respuesta
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            is_active=conversation.is_active,
            message_count=len(message_responses),
            messages=message_responses
        )
    
    def update_conversation_title(
        self, 
        db: Session, 
        user: User, 
        session_id: str, 
        new_title: str
    ) -> Optional[Conversation]:
        """Actualizar título de conversación"""
        
        conversation = self.get_conversation_by_session_id(db, user, session_id)
        if not conversation:
            return None
        
        conversation.title = new_title
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(conversation)
        
        return conversation
    
    def delete_conversation(
        self, 
        db: Session, 
        user: User, 
        session_id: str
    ) -> bool:
        """Eliminar conversación (soft delete)"""
        
        conversation = self.get_conversation_by_session_id(db, user, session_id)
        if not conversation:
            return False
        
        conversation.is_active = False
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        return True
    
    def add_message_to_conversation(
        self, 
        db: Session, 
        user: User, 
        session_id: str, 
        role: str, 
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Message]:
        """Agregar mensaje a una conversación existente"""
        
        conversation = self.get_conversation_by_session_id(db, user, session_id)
        if not conversation:
            return None
        
        # Usar el memory service para agregar el mensaje
        try:
            self.memory_service.add_message(db, session_id, role, content, metadata)
            
            # Actualizar timestamp de la conversación
            conversation.updated_at = datetime.utcnow()
            db.commit()
            
            # Obtener el mensaje recién creado
            latest_message = db.query(Message).filter(
                Message.conversation_id == conversation.id
            ).order_by(desc(Message.timestamp)).first()
            
            return latest_message
            
        except Exception as e:
            print(f"Error adding message to conversation: {e}")
            return None
    
    def get_or_create_conversation(
        self, 
        db: Session, 
        user: User, 
        session_id: Optional[str] = None
    ) -> Conversation:
        """Obtener conversación existente o crear una nueva"""
        
        if session_id:
            # Intentar obtener conversación existente
            conversation = self.get_conversation_by_session_id(db, user, session_id)
            if conversation:
                return conversation
        
        # Crear nueva conversación
        conversation_data = ConversationCreate(title=None)
        return self.create_conversation(db, user, conversation_data)
    
    def generate_conversation_title(
        self, 
        db: Session, 
        session_id: str, 
        first_message: str
    ) -> str:
        """Generar título automático basado en el primer mensaje"""
        
        # Título simple basado en las primeras palabras
        words = first_message.split()[:6]  # Primeras 6 palabras
        title = " ".join(words)
        
        # Limpiar y limitar longitud
        if len(title) > 50:
            title = title[:47] + "..."
        
        # Si está vacío, usar timestamp
        if not title.strip():
            title = f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        return title
    
    def update_conversation_from_first_message(
        self, 
        db: Session, 
        user: User, 
        session_id: str, 
        first_message: str
    ):
        """Actualizar título de conversación basado en el primer mensaje"""
        
        conversation = self.get_conversation_by_session_id(db, user, session_id)
        if not conversation:
            return
        
        # Solo actualizar si el título es genérico (contiene "Chat" y fecha)
        if "Chat" in conversation.title and "/" in conversation.title:
            new_title = self.generate_conversation_title(db, session_id, first_message)
            conversation.title = new_title
            conversation.updated_at = datetime.utcnow()
            db.commit()
    
    def get_conversation_analytics(
        self, 
        db: Session, 
        user: User,
        days: int = 30
    ) -> Dict[str, Any]:
        """Obtener análisis detallado de conversaciones del usuario"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Conversaciones en el período
        conversations = db.query(Conversation).filter(
            Conversation.user_id == user.id,
            Conversation.is_active == True,
            Conversation.created_at >= cutoff_date
        ).all()
        
        if not conversations:
            return {
                "period_days": days,
                "total_conversations": 0,
                "total_messages": 0,
                "daily_activity": [],
                "conversation_lengths": [],
                "most_active_hours": []
            }
        
        # Mensajes por día
        daily_activity = {}
        conversation_lengths = []
        hourly_activity = [0] * 24
        
        for conv in conversations:
            # Contar mensajes por conversación
            message_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
            conversation_lengths.append(message_count)
            
            # Actividad por día
            day_key = conv.created_at.date().isoformat()
            daily_activity[day_key] = daily_activity.get(day_key, 0) + 1
            
            # Actividad por hora
            hour = conv.created_at.hour
            hourly_activity[hour] += 1
        
        # Convertir daily_activity a lista ordenada
        daily_list = []
        current_date = cutoff_date.date()
        end_date = datetime.utcnow().date()
        
        while current_date <= end_date:
            day_key = current_date.isoformat()
            daily_list.append({
                "date": day_key,
                "conversations": daily_activity.get(day_key, 0)
            })
            current_date += timedelta(days=1)
        
        # Horas más activas
        most_active_hours = []
        for hour, count in enumerate(hourly_activity):
            if count > 0:
                most_active_hours.append({"hour": hour, "conversations": count})
        
        most_active_hours.sort(key=lambda x: x["conversations"], reverse=True)
        
        return {
            "period_days": days,
            "total_conversations": len(conversations),
            "total_messages": sum(conversation_lengths),
            "average_messages_per_conversation": round(sum(conversation_lengths) / len(conversations), 2) if conversations else 0,
            "daily_activity": daily_list,
            "conversation_lengths": {
                "min": min(conversation_lengths) if conversation_lengths else 0,
                "max": max(conversation_lengths) if conversation_lengths else 0,
                "average": round(sum(conversation_lengths) / len(conversation_lengths), 2) if conversation_lengths else 0
            },
            "most_active_hours": most_active_hours[:5]  # Top 5 horas
        }
    
    def search_messages(
        self, 
        db: Session, 
        user: User, 
        query: str,
        limit: int = 50
    ) -> List[Tuple[MessageResponse, ConversationResponse]]:
        """Buscar mensajes específicos en todas las conversaciones del usuario"""
        
        # Buscar mensajes que contengan el query
        messages = db.query(Message).join(Conversation).filter(
            Conversation.user_id == user.id,
            Conversation.is_active == True,
            Message.content.ilike(f"%{query}%")
        ).order_by(desc(Message.timestamp)).limit(limit).all()
        
        # Crear respuestas con información de conversación
        results = []
        for message in messages:
            conversation = message.conversation
            
            message_response = MessageResponse(
                id=message.id,
                conversation_id=message.conversation_id,
                role=message.role,
                content=message.content,
                timestamp=message.timestamp,
                message_metadata=message.message_metadata
            )
            
            conversation_response = ConversationResponse(
                id=conversation.id,
                session_id=conversation.session_id,
                user_id=conversation.user_id,
                project_id=conversation.project_id,  # Incluir project_id en la respuesta
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                is_active=conversation.is_active,
                message_count=0  # No necesario para este contexto
            )
            
            results.append((message_response, conversation_response))
        
        return results
    
    def get_contextual_conversation_summary(
        self, 
        db: Session, 
        user: User, 
        session_id: str
    ) -> Dict[str, Any]:
        """Obtener resumen contextual de una conversación para mejorar respuestas futuras"""
        
        conversation = self.get_conversation_by_session_id(db, user, session_id)
        if not conversation:
            return {}
        
        # Obtener todos los mensajes de la conversación
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(Message.timestamp).all()
        
        if not messages:
            return {}
        
        # Extraer información contextual clave
        context_summary = {
            "conversation_id": conversation.id,
            "session_id": session_id,
            "project_id": conversation.project_id,  # Incluir project_id en el resumen
            "total_messages": len(messages),
            "duration_minutes": self._calculate_conversation_duration(messages),
            "topics_discussed": self._extract_topics_from_messages(messages),
            "user_preferences": self._extract_user_preferences(messages),
            "conversation_flow": self._analyze_conversation_flow(messages),
            "key_decisions": self._extract_key_decisions(messages),
            "unresolved_questions": self._find_unresolved_questions(messages),
            "company_context": self._extract_company_context(db, user, messages)
        }
        
        return context_summary
    
    def get_cross_conversation_context(
        self, 
        db: Session, 
        user: User, 
        current_session_id: str,
        context_limit: int = 5
    ) -> Dict[str, Any]:
        """Obtener contexto relevante de conversaciones anteriores del usuario"""
        
        # Obtener conversaciones recientes del usuario (excluyendo la actual)
        recent_conversations = db.query(Conversation).filter(
            Conversation.user_id == user.id,
            Conversation.session_id != current_session_id,
            Conversation.is_active == True
        ).order_by(desc(Conversation.updated_at)).limit(context_limit).all()
        
        cross_context = {
            "user_id": user.id,
            "company_id": user.company_id,
            "work_area": user.work_area,
            "recent_conversations": [],
            "recurring_themes": [],
            "established_preferences": {},
            "ongoing_projects": [],
            "historical_decisions": []
        }
        
        for conv in recent_conversations:
            conv_summary = self.get_contextual_conversation_summary(db, user, conv.session_id)
            if conv_summary:
                cross_context["recent_conversations"].append({
                    "session_id": conv.session_id,
                    "title": conv.title,
                    "date": conv.updated_at,
                    "topics": conv_summary.get("topics_discussed", []),
                    "key_decisions": conv_summary.get("key_decisions", [])
                })
        
        # Analizar patrones entre conversaciones
        cross_context["recurring_themes"] = self._find_recurring_themes(cross_context["recent_conversations"])
        cross_context["established_preferences"] = self._consolidate_user_preferences(cross_context["recent_conversations"])
        
        return cross_context
    
    def get_intelligent_conversation_suggestions(
        self, 
        db: Session, 
        user: User, 
        current_message: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generar sugerencias inteligentes basadas en el contexto del usuario"""
        
        suggestions = {
            "follow_up_questions": [],
            "related_topics": [],
            "previous_discussions": [],
            "company_specific_insights": [],
            "action_items": []
        }
        
        # Obtener contexto de la conversación actual
        if session_id:
            current_context = self.get_contextual_conversation_summary(db, user, session_id)
            suggestions["current_context"] = current_context
        
        # Obtener contexto de conversaciones anteriores
        cross_context = self.get_cross_conversation_context(db, user, session_id or "")
        
        # Generar sugerencias basadas en patrones históricos
        suggestions["follow_up_questions"] = self._generate_contextual_follow_ups(
            current_message, cross_context
        )
        
        suggestions["related_topics"] = self._suggest_related_topics(
            current_message, cross_context["recurring_themes"]
        )
        
        suggestions["previous_discussions"] = self._find_related_previous_discussions(
            current_message, cross_context["recent_conversations"]
        )
        
        # Sugerencias específicas de la compañía
        if user.company_id:
            suggestions["company_specific_insights"] = self._generate_company_insights(
                db, user.company_id, current_message
            )
        
        return suggestions
    
    def update_conversation_context_metadata(
        self, 
        db: Session, 
        session_id: str, 
        context_metadata: Dict[str, Any]
    ):
        """Actualizar metadatos de contexto de una conversación"""
        
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if conversation:
            # Actualizar o crear metadatos de contexto
            if not hasattr(conversation, 'context_metadata'):
                conversation.context_metadata = {}
            
            conversation.context_metadata.update(context_metadata)
            conversation.updated_at = datetime.utcnow()
            db.commit()
    
    def _calculate_conversation_duration(self, messages: List[Message]) -> int:
        """Calcular duración de la conversación en minutos"""
        if len(messages) < 2:
            return 0
        
        start_time = messages[0].timestamp
        end_time = messages[-1].timestamp
        duration = end_time - start_time
        return int(duration.total_seconds() / 60)
    
    def _extract_topics_from_messages(self, messages: List[Message]) -> List[str]:
        """Extraer temas principales de los mensajes"""
        topics = []
        
        # Palabras clave comunes en contexto empresarial
        business_keywords = {
            "estrategia": "Estrategia empresarial",
            "marketing": "Marketing y ventas",
            "producto": "Desarrollo de producto",
            "equipo": "Gestión de equipos",
            "finanzas": "Finanzas y presupuesto",
            "tecnología": "Tecnología e innovación",
            "clientes": "Experiencia del cliente",
            "competencia": "Análisis competitivo",
            "crecimiento": "Crecimiento y expansión",
            "operaciones": "Operaciones y procesos"
        }
        
        for message in messages:
            content_lower = message.content.lower()
            for keyword, topic in business_keywords.items():
                if keyword in content_lower and topic not in topics:
                    topics.append(topic)
        
        return topics[:5]  # Limitar a 5 temas principales
    
    def _extract_user_preferences(self, messages: List[Message]) -> Dict[str, Any]:
        """Extraer preferencias del usuario de los mensajes"""
        preferences = {
            "communication_style": "professional",
            "detail_level": "medium",
            "preferred_formats": [],
            "industry_focus": [],
            "decision_making_style": "analytical"
        }
        
        user_messages = [msg for msg in messages if msg.role == "user"]
        
        # Analizar estilo de comunicación
        total_words = sum(len(msg.content.split()) for msg in user_messages)
        avg_message_length = total_words / len(user_messages) if user_messages else 0
        
        if avg_message_length > 50:
            preferences["detail_level"] = "high"
        elif avg_message_length < 20:
            preferences["detail_level"] = "low"
        
        return preferences
    
    def _analyze_conversation_flow(self, messages: List[Message]) -> Dict[str, Any]:
        """Analizar el flujo de la conversación"""
        flow_analysis = {
            "question_to_answer_ratio": 0,
            "clarification_requests": 0,
            "topic_changes": 0,
            "engagement_level": "medium"
        }
        
        questions = 0
        clarifications = 0
        
        for message in messages:
            if message.role == "user":
                if "?" in message.content:
                    questions += 1
                if any(word in message.content.lower() for word in ["aclarar", "explicar", "no entiendo"]):
                    clarifications += 1
        
        flow_analysis["question_to_answer_ratio"] = questions / len(messages) if messages else 0
        flow_analysis["clarification_requests"] = clarifications
        
        return flow_analysis
    
    def _extract_key_decisions(self, messages: List[Message]) -> List[str]:
        """Extraer decisiones clave mencionadas en la conversación"""
        decisions = []
        
        decision_indicators = [
            "decidimos", "vamos a", "implementaremos", "elegimos",
            "optamos por", "acordamos", "definimos", "establecemos"
        ]
        
        for message in messages:
            content_lower = message.content.lower()
            for indicator in decision_indicators:
                if indicator in content_lower:
                    # Extraer la oración que contiene la decisión
                    sentences = message.content.split('.')
                    for sentence in sentences:
                        if indicator in sentence.lower():
                            decisions.append(sentence.strip())
                            break
        
        return decisions[:3]  # Limitar a 3 decisiones principales
    
    def _find_unresolved_questions(self, messages: List[Message]) -> List[str]:
        """Encontrar preguntas sin resolver en la conversación"""
        unresolved = []
        
        user_questions = []
        for message in messages:
            if message.role == "user" and "?" in message.content:
                user_questions.append(message.content)
        
        # Simplificación: asumir que las últimas preguntas pueden estar sin resolver
        if len(user_questions) > 0:
            unresolved = user_questions[-2:]  # Últimas 2 preguntas
        
        return unresolved
    
    def _extract_company_context(self, db: Session, user: User, messages: List[Message]) -> Dict[str, Any]:
        """Extraer contexto específico de la compañía"""
        company_context = {}
        
        if user.company_id:
            try:
                from app.services.company_service import CompanyService
                company = CompanyService.get_company_by_id(db, user.company_id)
                
                if company:
                    company_context = {
                        "company_name": company.name,
                        "industry": company.industry,
                        "sector": company.sector,
                        "user_work_area": user.work_area
                    }
            except Exception as e:
                print(f"Error extracting company context: {e}")
        
        return company_context
    
    def _find_recurring_themes(self, conversations: List[Dict]) -> List[str]:
        """Encontrar temas recurrentes entre conversaciones"""
        theme_count = {}
        
        for conv in conversations:
            for topic in conv.get("topics", []):
                theme_count[topic] = theme_count.get(topic, 0) + 1
        
        # Retornar temas que aparecen en más de una conversación
        recurring = [theme for theme, count in theme_count.items() if count > 1]
        return sorted(recurring, key=lambda x: theme_count[x], reverse=True)
    
    def _consolidate_user_preferences(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Consolidar preferencias del usuario de múltiples conversaciones"""
        consolidated = {
            "preferred_topics": [],
            "communication_patterns": {},
            "decision_factors": []
        }
        
        # Analizar patrones de temas preferidos
        topic_frequency = {}
        for conv in conversations:
            for topic in conv.get("topics", []):
                topic_frequency[topic] = topic_frequency.get(topic, 0) + 1
        
        consolidated["preferred_topics"] = sorted(
            topic_frequency.keys(), 
            key=lambda x: topic_frequency[x], 
            reverse=True
        )[:5]
        
        return consolidated
    
    def _generate_contextual_follow_ups(self, current_message: str, cross_context: Dict) -> List[str]:
        """Generar preguntas de seguimiento contextualmente relevantes"""
        follow_ups = []
        
        # Basado en temas recurrentes
        for theme in cross_context.get("recurring_themes", [])[:3]:
            follow_ups.append(f"¿Cómo se relaciona esto con {theme.lower()}?")
        
        # Basado en el área de trabajo del usuario
        work_area = cross_context.get("work_area")
        if work_area:
            follow_ups.append(f"¿Cómo impacta esto en tu área de {work_area}?")
        
        return follow_ups[:3]
    
    def _suggest_related_topics(self, current_message: str, recurring_themes: List[str]) -> List[str]:
        """Sugerir temas relacionados basados en el historial"""
        related = []
        
        message_lower = current_message.lower()
        
        # Mapeo de temas relacionados
        topic_relations = {
            "estrategia": ["Marketing y ventas", "Crecimiento y expansión"],
            "marketing": ["Experiencia del cliente", "Análisis competitivo"],
            "producto": ["Tecnología e innovación", "Experiencia del cliente"],
            "equipo": ["Operaciones y procesos", "Crecimiento y expansión"]
        }
        
        for keyword, related_topics in topic_relations.items():
            if keyword in message_lower:
                for topic in related_topics:
                    if topic in recurring_themes and topic not in related:
                        related.append(topic)
        
        return related[:3]
    
    def _find_related_previous_discussions(self, current_message: str, recent_conversations: List[Dict]) -> List[Dict]:
        """Encontrar discusiones previas relacionadas"""
        related_discussions = []
        
        message_words = set(current_message.lower().split())
        
        for conv in recent_conversations:
            # Calcular similitud básica basada en palabras comunes
            conv_topics = conv.get("topics", [])
            topic_words = set(" ".join(conv_topics).lower().split())
            
            common_words = message_words.intersection(topic_words)
            if len(common_words) >= 2:  # Al menos 2 palabras en común
                related_discussions.append({
                    "session_id": conv["session_id"],
                    "title": conv["title"],
                    "date": conv["date"],
                    "relevance_score": len(common_words)
                })
        
        # Ordenar por relevancia
        related_discussions.sort(key=lambda x: x["relevance_score"], reverse=True)
        return related_discussions[:2]
    
    def _generate_company_insights(self, db: Session, company_id: int, current_message: str) -> List[str]:
        """Generar insights específicos de la compañía"""
        insights = []
        
        try:
            from app.services.company_service import CompanyService
            company = CompanyService.get_company_by_id(db, company_id)
            
            if company:
                # Insights basados en la industria
                industry_insights = {
                    "tecnología": [
                        "Considera el impacto en la escalabilidad técnica",
                        "Evalúa las implicaciones de seguridad y privacidad"
                    ],
                    "marketing": [
                        "Analiza el impacto en la experiencia del cliente",
                        "Considera las métricas de conversión y ROI"
                    ],
                    "finanzas": [
                        "Evalúa el impacto financiero y el flujo de caja",
                        "Considera los riesgos regulatorios y de compliance"
                    ]
                }
                
                industry_key = company.industry.lower()
                if industry_key in industry_insights:
                    insights.extend(industry_insights[industry_key])
        
        except Exception as e:
            print(f"Error generating company insights: {e}")
        
        return insights[:2]
