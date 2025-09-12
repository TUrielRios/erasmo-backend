"""
Servicio para gestión de sesiones de chat y conversaciones por usuario
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from datetime import datetime, timedelta
import uuid

from app.models.conversation import User, Conversation, Message
from app.models.schemas import ConversationCreate, ConversationResponse, ConversationWithMessages, MessageResponse
from app.services.memory_service import MemoryService

class ChatService:
    """Servicio para gestión de chats y sesiones por usuario"""
    
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
        
        # Crear conversación
        db_conversation = Conversation(
            session_id=session_id,
            user_id=user.id,
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
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                is_active=conversation.is_active,
                message_count=0  # No necesario para este contexto
            )
            
            results.append((message_response, conversation_response))
        
        return results
