"""
Endpoints para gestión de chats y conversaciones - sin autenticación JWT
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from app.services.chat_service import ChatService
from app.models.user import User
from app.models.conversation import Message, Conversation
from app.models.schemas import (
    ConversationCreate, 
    ConversationResponse, 
    ConversationWithMessages,
    MessageResponse,
    MessageUpdate,
    MessageDeleteResponse
)
from app.services.auth_service import AuthService
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()
conversation_service = ConversationService()

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    user_id: int,  # Now requires user_id as parameter
    db: Session = Depends(get_db)
):
    """Crear nueva conversación - requiere user_id"""
    try:
        # Get user from database
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        conversation = chat_service.create_conversation(db, current_user, conversation_data)
        
        return ConversationResponse(
            id=conversation.id,
            session_id=conversation.session_id,
            user_id=conversation.user_id,
            project_id=conversation.project_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            is_active=conversation.is_active,
            message_count=0
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando conversación: {str(e)}"
        )

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(
    user_id: int,  # Now requires user_id as parameter
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Obtener todas las conversaciones del usuario - requiere user_id"""
    try:
        # Get user from database
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        conversations = chat_service.get_user_conversations(db, current_user, skip, limit)
        return conversations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo conversaciones: {str(e)}"
        )

@router.get("/conversations/{session_id}", response_model=ConversationWithMessages)
async def get_conversation_with_messages(
    session_id: str,
    user_id: int,  # Now requires user_id as parameter
    message_limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Obtener conversación completa con mensajes"""
    try:
        # Get user from database
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        conversation = chat_service.get_conversation_with_messages(
            db, current_user, session_id, message_limit
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversación no encontrada"
            )
        
        return conversation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo conversación: {str(e)}"
        )

@router.put("/conversations/{session_id}/title")
async def update_conversation_title(
    session_id: str,
    new_title: str,
    user_id: int,  # Now requires user_id as parameter
    db: Session = Depends(get_db)
):
    """Actualizar título de conversación"""
    try:
        # Get user from database
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        conversation = chat_service.update_conversation_title(
            db, current_user, session_id, new_title
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversación no encontrada"
            )
        
        return {"message": "Título actualizado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando título: {str(e)}"
        )

@router.delete("/conversations/{session_id}")
async def delete_conversation(
    session_id: str,
    user_id: int,  # Now requires user_id as parameter
    db: Session = Depends(get_db)
):
    """Eliminar conversación"""
    try:
        # Get user from database
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        success = chat_service.delete_conversation(db, current_user, session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversación no encontrada"
            )
        
        return {"message": "Conversación eliminada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando conversación: {str(e)}"
        )

@router.get("/search", response_model=List[ConversationResponse])
async def search_conversations(
    user_id: int,  # Now requires user_id as parameter
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Buscar conversaciones por contenido o título"""
    try:
        # Get user from database
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        # Buscar en títulos de conversaciones
        title_matches = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True,
            Conversation.title.ilike(f"%{q}%")
        ).offset(skip).limit(limit).all()
        
        # Buscar en contenido de mensajes
        message_matches = db.query(Conversation).join(Message).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True,
            Message.content.ilike(f"%{q}%")
        ).distinct().offset(skip).limit(limit).all()
        
        # Combinar resultados sin duplicados
        all_conversations = {conv.id: conv for conv in title_matches + message_matches}
        
        # Convertir a response con conteo de mensajes
        result = []
        for conv in all_conversations.values():
            message_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
            
            conv_response = ConversationResponse(
                id=conv.id,
                session_id=conv.session_id,
                user_id=conv.user_id,
                project_id=conv.project_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                is_active=conv.is_active,
                message_count=message_count
            )
            result.append(conv_response)
        
        # Ordenar por fecha de actualización
        result.sort(key=lambda x: x.updated_at or x.created_at, reverse=True)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error buscando conversaciones: {str(e)}"
        )

@router.get("/recent", response_model=List[ConversationResponse])
async def get_recent_conversations(
    user_id: int,  # Now requires user_id as parameter
    days: int = Query(7, ge=1, le=365, description="Días hacia atrás"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Obtener conversaciones recientes del usuario"""
    try:
        # Get user from database
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True,
            Conversation.updated_at >= cutoff_date
        ).order_by(Conversation.updated_at.desc()).limit(limit).all()
        
        # Convertir a response con conteo de mensajes
        result = []
        for conv in conversations:
            message_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
            
            conv_response = ConversationResponse(
                id=conv.id,
                session_id=conv.session_id,
                user_id=conv.user_id,
                project_id=conv.project_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                is_active=conv.is_active,
                message_count=message_count
            )
            result.append(conv_response)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo conversaciones recientes: {str(e)}"
        )

@router.get("/stats")
async def get_user_chat_stats(
    user_id: int,  # Now requires user_id as parameter
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de chat del usuario"""
    try:
        # Get user from database
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        # Estadísticas básicas
        total_conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True
        ).count()
        
        total_messages = db.query(Message).join(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True
        ).count()
        
        # Conversaciones por mes (últimos 6 meses)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        recent_conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True,
            Conversation.created_at >= six_months_ago
        ).count()
        
        # Mensajes por rol
        user_messages = db.query(Message).join(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True,
            Message.role == "user"
        ).count()
        
        assistant_messages = db.query(Message).join(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True,
            Message.role == "assistant"
        ).count()
        
        # Conversación más activa
        most_active_conv = db.query(Conversation).join(Message).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True
        ).group_by(Conversation.id).order_by(
            db.func.count(Message.id).desc()
        ).first()
        
        most_active_title = most_active_conv.title if most_active_conv else None
        most_active_messages = db.query(Message).filter(
            Message.conversation_id == most_active_conv.id
        ).count() if most_active_conv else 0
        
        return {
            "user_id": current_user.id,
            "username": current_user.username,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "recent_conversations_6m": recent_conversations,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "most_active_conversation": {
                "title": most_active_title,
                "message_count": most_active_messages
            },
            "average_messages_per_conversation": round(total_messages / total_conversations, 2) if total_conversations > 0 else 0,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )

@router.get("/export/{session_id}")
async def export_conversation(
    session_id: str,
    user_id: int,  # Now requires user_id as parameter
    format: str = Query("json", regex="^(json|txt|md)$"),
    db: Session = Depends(get_db)
):
    """Exportar conversación en diferentes formatos"""
    try:
        # Get user from database
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        conversation_with_messages = chat_service.get_conversation_with_messages(
            db, current_user, session_id
        )
        
        if not conversation_with_messages:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversación no encontrada"
            )
        
        if format == "json":
            return {
                "conversation": conversation_with_messages.dict(),
                "exported_at": datetime.utcnow(),
                "format": "json"
            }
        
        elif format == "txt":
            content = f"Conversación: {conversation_with_messages.title}\n"
            content += f"Creada: {conversation_with_messages.created_at}\n"
            content += f"Mensajes: {len(conversation_with_messages.messages)}\n"
            content += "=" * 50 + "\n\n"
            
            for msg in conversation_with_messages.messages:
                role_label = "Usuario" if msg.role == "user" else "Asistente"
                content += f"[{msg.timestamp}] {role_label}:\n{msg.content}\n\n"
            
            return {"content": content, "format": "txt"}
        
        elif format == "md":
            content = f"# {conversation_with_messages.title}\n\n"
            content += f"**Creada:** {conversation_with_messages.created_at}  \n"
            content += f"**Mensajes:** {len(conversation_with_messages.messages)}  \n\n"
            content += "---\n\n"
            
            for msg in conversation_with_messages.messages:
                role_label = "👤 Usuario" if msg.role == "user" else "🤖 Asistente"
                content += f"## {role_label}\n"
                content += f"*{msg.timestamp}*\n\n"
                content += f"{msg.content}\n\n"
            
            return {"content": content, "format": "markdown"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exportando conversación: {str(e)}"
        )

@router.put("/messages/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: int,
    message_update: MessageUpdate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Actualizar contenido de un mensaje enviado"""
    try:
        # Get user from database
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        # Update the message
        updated_message = chat_service.update_message(
            db, current_user, message_id, message_update.content
        )
        
        if not updated_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mensaje no encontrado o no tienes permiso para editarlo"
            )
        
        return MessageResponse(
            id=updated_message.id,
            conversation_id=updated_message.conversation_id,
            role=updated_message.role,
            content=updated_message.content,
            timestamp=updated_message.timestamp,
            message_metadata=updated_message.message_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando mensaje: {str(e)}"
        )

@router.delete("/messages/{message_id}", response_model=MessageDeleteResponse)
async def delete_message(
    message_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar un mensaje enviado"""
    try:
        # Get user from database
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        # Delete the message
        success = chat_service.delete_message(db, current_user, message_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mensaje no encontrado o no tienes permiso para eliminarlo"
            )
        
        return MessageDeleteResponse(
            success=True,
            message="Mensaje eliminado exitosamente",
            deleted_message_id=message_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error eliminando mensaje: {str(e)}"
        )

@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Obtener un mensaje específico"""
    try:
        # Get user from database
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        # Get the message
        message = chat_service.get_message_by_id(db, current_user, message_id)
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mensaje no encontrado"
            )
        
        return MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            timestamp=message.timestamp,
            message_metadata=message.message_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo mensaje: {str(e)}"
        )
