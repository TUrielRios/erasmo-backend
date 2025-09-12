"""
Servicio para manejo de memoria conversacional completa
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
import uuid
from datetime import datetime

from app.db.database import get_db
from app.models.conversation import Conversation, Message

class MemoryService:
    """Servicio para gestionar memoria conversacional completa"""
    
    def __init__(self, default_memory_limit: int = 200):  # Aumentado de 30 a 200 mensajes
        """
        Inicializa el servicio de memoria
        
        Args:
            default_memory_limit: Número por defecto de mensajes a recordar
        """
        self.default_memory_limit = default_memory_limit
    
    def get_or_create_conversation(self, db: Session, session_id: str = None) -> Conversation:
        """Obtiene o crea una conversación"""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.is_active == True
        ).first()
        
        if not conversation:
            conversation = Conversation(
                session_id=session_id,
                title="Nueva Conversación",
                is_active=True
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            print(f"✅ Nueva conversación creada: {session_id}")
        
        return conversation
    
    def add_message(self, db: Session, session_id: str, role: str, content: str, metadata: Dict = None) -> Message:
        """
        Añade un mensaje a la conversación
        
        Args:
            db: Sesión de base de datos
            session_id: ID de la sesión
            role: Rol del mensaje ('user' o 'assistant')
            content: Contenido del mensaje
            metadata: Metadatos adicionales del mensaje
        """
        conversation = self.get_or_create_conversation(db, session_id)
        
        # Preparar metadatos con timestamp y información adicional
        message_metadata = {
            "created_at": datetime.utcnow().isoformat(),
            "message_length": len(content),
            "session_id": session_id
        }
        
        if metadata:
            message_metadata.update(metadata)
        
        message = Message(
            conversation_id=conversation.id,
            role=role,
            content=content,
            message_metadata=json.dumps(message_metadata)
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Actualizar título de conversación si es el primer mensaje del usuario
        if role == "user" and conversation.title == "Nueva Conversación":
            title = content[:50] + "..." if len(content) > 50 else content
            conversation.title = title
            db.commit()
        
        # Limpiar mensajes antiguos si excedemos el límite de memoria
        self._cleanup_old_messages(db, conversation.id)
        
        print(f"✅ Mensaje añadido: {role} - {len(content)} caracteres")
        return message
    
    def get_conversation_history(self, db: Session, session_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Obtiene el historial completo de una conversación
        
        Args:
            db: Sesión de base de datos
            session_id: ID de la sesión
            limit: Límite de mensajes (por defecto usa self.default_memory_limit)
        """
        if limit is None:
            limit = self.default_memory_limit
        
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.is_active == True
        ).first()
        
        if not conversation:
            return []
        
        # Obtener los últimos N mensajes ordenados cronológicamente
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id
        ).order_by(desc(Message.timestamp)).limit(limit).all()
        
        # Revertir para tener orden cronológico correcto
        messages.reverse()
        
        history = []
        for message in messages:
            metadata = self._parse_message_metadata(message.message_metadata)
            
            history.append({
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "metadata": metadata
            })
        
        return history
    
    def get_full_context_for_ai(self, db: Session, session_id: str, 
                               include_system_info: bool = True,
                               memory_limit: int = None) -> Dict[str, Any]:
        """
        Obtiene el contexto completo formateado para el AI
        
        Args:
            db: Sesión de base de datos
            session_id: ID de la sesión
            include_system_info: Si incluir información del sistema
            memory_limit: Límite de mensajes a incluir
        
        Returns:
            Diccionario con el contexto completo
        """
        if memory_limit is None:
            memory_limit = self.default_memory_limit
            
        history = self.get_conversation_history(db, session_id, memory_limit)
        
        if not history:
            return {
                "messages": [],
                "context_summary": "Nueva conversación sin historial previo",
                "message_count": 0,
                "session_info": {
                    "session_id": session_id,
                    "is_new_session": True
                }
            }
        
        # Formatear mensajes para el AI
        formatted_messages = []
        for msg in history:
            role_label = "Usuario" if msg["role"] == "user" else "Asistente"
            formatted_messages.append({
                "role": msg["role"],
                "role_label": role_label,
                "content": msg["content"],
                "timestamp": msg["timestamp"],
                "id": msg["id"]
            })
        
        # Generar resumen del contexto
        context_summary = self._generate_context_summary(history)
        
        # Información de la sesión
        session_info = {
            "session_id": session_id,
            "is_new_session": False,
            "total_messages": len(history),
            "memory_limit": memory_limit,
            "oldest_message": history[0]["timestamp"] if history else None,
            "newest_message": history[-1]["timestamp"] if history else None
        }
        
        result = {
            "messages": formatted_messages,
            "context_summary": context_summary,
            "message_count": len(history),
            "session_info": session_info
        }
        
        if include_system_info:
            result["system_info"] = self._get_system_info(db, session_id)
        
        return result
    
    def get_conversation_summary(self, db: Session, session_id: str) -> Dict[str, Any]:
        """
        Obtiene un resumen de la conversación actual
        """
        history = self.get_conversation_history(db, session_id)
        
        if not history:
            return {
                "summary": "Conversación nueva sin mensajes",
                "stats": {
                    "total_messages": 0,
                    "user_messages": 0,
                    "assistant_messages": 0
                }
            }
        
        user_messages = [msg for msg in history if msg["role"] == "user"]
        assistant_messages = [msg for msg in history if msg["role"] == "assistant"]
        
        # Calcular estadísticas
        stats = {
            "total_messages": len(history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "avg_user_message_length": sum(len(msg["content"]) for msg in user_messages) / len(user_messages) if user_messages else 0,
            "avg_assistant_message_length": sum(len(msg["content"]) for msg in assistant_messages) / len(assistant_messages) if assistant_messages else 0,
            "conversation_start": history[0]["timestamp"] if history else None,
            "last_activity": history[-1]["timestamp"] if history else None
        }
        
        # Generar resumen narrativo
        summary = self._generate_conversation_summary(history, stats)
        
        return {
            "summary": summary,
            "stats": stats,
            "recent_topics": self._extract_recent_topics(history[-10:])  # Últimos 10 mensajes
        }
    
    def search_in_conversation(self, db: Session, session_id: str, 
                              search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca mensajes que contengan un término específico
        """
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.is_active == True
        ).first()
        
        if not conversation:
            return []
        
        messages = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.content.contains(search_term)
        ).order_by(desc(Message.timestamp)).limit(limit).all()
        
        results = []
        for message in messages:
            metadata = self._parse_message_metadata(message.message_metadata)
            results.append({
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "timestamp": message.timestamp.isoformat(),
                "metadata": metadata,
                "relevance_context": self._get_message_context(db, message.id, context_size=2)
            })
        
        return results
    
    def update_memory_limit(self, new_limit: int):
        """Actualiza el límite de memoria por defecto"""
        self.default_memory_limit = max(10, new_limit)  # Mínimo 10 mensajes
        print(f"✅ Límite de memoria actualizado a {self.default_memory_limit} mensajes")
    
    def clear_conversation(self, db: Session, session_id: str) -> bool:
        """Marca una conversación como inactiva"""
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if conversation:
            conversation.is_active = False
            db.commit()
            print(f"✅ Conversación {session_id} marcada como inactiva")
            return True
        
        return False
    
    def _cleanup_old_messages(self, db: Session, conversation_id: int):
        """Limpia mensajes antiguos que excedan el límite de memoria"""
        return  # No hacer limpieza automática
        
        # Código original comentado para mantener la funcionalidad si se necesita
        # total_messages = db.query(Message).filter(
        #     Message.conversation_id == conversation_id
        # ).count()
        # 
        # # Si excedemos el límite, eliminar los mensajes más antiguos
        # if total_messages > self.default_memory_limit * 1.5:  # Permitir un 50% extra antes de limpiar
        #     messages_to_delete = total_messages - self.default_memory_limit
        #     
        #     old_messages = db.query(Message).filter(
        #         Message.conversation_id == conversation_id
        #     ).order_by(Message.timestamp).limit(messages_to_delete).all()
        #     
        #     for message in old_messages:
        #         db.delete(message)
        #     
        #     db.commit()
        #     print(f"🧹 Limpiados {messages_to_delete} mensajes antiguos")
    
    def _parse_message_metadata(self, metadata_json: str) -> Dict[str, Any]:
        """Parse metadata JSON de forma segura"""
        if not metadata_json:
            return {}
        
        try:
            if isinstance(metadata_json, str):
                return json.loads(metadata_json)
            elif isinstance(metadata_json, dict):
                return metadata_json
            else:
                return {}
        except (json.JSONDecodeError, TypeError, AttributeError):
            return {}
    
    def _generate_context_summary(self, history: List[Dict[str, Any]]) -> str:
        """Genera un resumen del contexto de la conversación"""
        if not history:
            return "Nueva conversación"
        
        user_messages = [msg for msg in history if msg["role"] == "user"]
        assistant_messages = [msg for msg in history if msg["role"] == "assistant"]
        
        summary_parts = [
            f"Conversación con {len(history)} mensajes totales",
            f"({len(user_messages)} del usuario, {len(assistant_messages)} del asistente)"
        ]
        
        if history:
            time_span = datetime.fromisoformat(history[-1]["timestamp"]) - datetime.fromisoformat(history[0]["timestamp"])
            if time_span.total_seconds() > 3600:  # Más de 1 hora
                summary_parts.append(f"Duración: {time_span.total_seconds()//3600:.0f}h {(time_span.total_seconds()%3600)//60:.0f}m")
            else:
                summary_parts.append(f"Duración: {time_span.total_seconds()//60:.0f}m")
        
        return ". ".join(summary_parts)
    
    def _generate_conversation_summary(self, history: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """Genera un resumen narrativo de la conversación"""
        if not history:
            return "Conversación vacía"
        
        # Tomar una muestra de mensajes para el resumen
        sample_size = min(5, len(history))
        recent_messages = history[-sample_size:]
        
        summary = f"Conversación activa con {stats['total_messages']} mensajes intercambiados. "
        
        if stats['user_messages'] > stats['assistant_messages']:
            summary += "El usuario ha sido muy participativo. "
        
        # Agregar información sobre temas recientes si es posible
        recent_topics = self._extract_recent_topics(recent_messages)
        if recent_topics:
            summary += f"Temas recientes: {', '.join(recent_topics[:3])}."
        
        return summary
    
    def _extract_recent_topics(self, recent_messages: List[Dict[str, Any]]) -> List[str]:
        """Extrae temas de mensajes recientes (implementación básica)"""
        topics = []
        
        # Esta es una implementación simple - en un caso real podrías usar NLP
        common_words = set(['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'me', 'si', 'muy', 'más', 'como', 'pero', 'sus', 'del', 'está', 'todo', 'una', 'ser', 'son', 'hacer', 'puede', 'tiene'])
        
        for msg in recent_messages:
            if msg["role"] == "user":
                words = msg["content"].lower().split()
                # Buscar palabras significativas (más de 3 caracteres, no comunes)
                significant_words = [w for w in words if len(w) > 3 and w not in common_words and w.isalpha()]
                topics.extend(significant_words[:2])  # Máximo 2 por mensaje
        
        # Devolver temas únicos
        return list(set(topics))[:5]  # Máximo 5 temas
    
    def _get_message_context(self, db: Session, message_id: int, context_size: int = 2) -> Dict[str, Any]:
        """Obtiene el contexto alrededor de un mensaje específico"""
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return {}
        
        # Obtener mensajes anteriores y posteriores
        before_messages = db.query(Message).filter(
            Message.conversation_id == message.conversation_id,
            Message.timestamp < message.timestamp
        ).order_by(desc(Message.timestamp)).limit(context_size).all()
        
        after_messages = db.query(Message).filter(
            Message.conversation_id == message.conversation_id,
            Message.timestamp > message.timestamp
        ).order_by(Message.timestamp).limit(context_size).all()
        
        return {
            "before": [{"role": msg.role, "content": msg.content[:100] + "..."} for msg in reversed(before_messages)],
            "after": [{"role": msg.role, "content": msg.content[:100] + "..."} for msg in after_messages]
        }
    
    def _get_system_info(self, db: Session, session_id: str) -> Dict[str, Any]:
        """Obtiene información del sistema para incluir en el contexto"""
        return {
            "memory_service_version": "2.0",
            "memory_limit": self.default_memory_limit,
            "features": [
                "full_conversation_memory",
                "context_search",
                "conversation_summary",
                "automatic_cleanup"
            ],
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def extract_key_info(self, db: Session, session_id: str, content: str) -> Dict[str, Any]:
        """
        Extrae información clave de un mensaje para almacenar en memoria
        
        Args:
            db: Sesión de base de datos
            session_id: ID de la sesión
            content: Contenido del mensaje a analizar
            
        Returns:
            Diccionario con información clave extraída
        """
        key_info = {
            "message_length": len(content),
            "word_count": len(content.split()),
            "has_questions": "?" in content,
            "has_numbers": any(char.isdigit() for char in content),
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id
        }
        
        # Extraer palabras clave básicas
        words = content.lower().split()
        common_words = {'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'me', 'si', 'muy', 'más', 'como', 'pero', 'sus', 'del', 'está', 'todo', 'una', 'ser', 'hacer', 'puede', 'tiene'}
        
        keywords = [word for word in words if len(word) > 3 and word not in common_words and word.isalpha()]
        key_info["keywords"] = keywords[:10]  # Top 10 keywords
        
        # Detectar temas comunes
        business_terms = ['marca', 'negocio', 'empresa', 'cliente', 'mercado', 'estrategia', 'marketing', 'ventas', 'producto', 'servicio']
        detected_topics = [term for term in business_terms if term in content.lower()]
        key_info["detected_topics"] = detected_topics
        
        return key_info
