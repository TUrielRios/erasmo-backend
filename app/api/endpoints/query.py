"""
Endpoints para consultas conversacionales con IA real
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import time
import uuid
from datetime import datetime

from app.models.schemas import (
    QueryRequest, 
    QueryResponse, 
    ResponseLevel,
    ConceptualResponse,
    AccionalResponse,
    ClarificationQuestion
)
from app.services.conversation_service import ConversationService
from app.services.memory_service import MemoryService
from app.services.chat_service import ChatService
from app.db.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_active_user
from app.models.conversation import User, Message  # Added missing Message import

router = APIRouter()

# Instancias globales de servicios
conversation_service = ConversationService()
memory_service = MemoryService()
chat_service = ChatService()

@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Procesa una consulta del usuario autenticado y devuelve respuesta estratégica usando IA real
    con persistencia de mensajes en base de datos
    """
    
    start_time = time.time()
    
    try:
        print(f"[DEBUG] Processing query for user {current_user.id}: {request.message[:50]}...")
        
        if request.session_id:
            conversation = chat_service.get_conversation_by_session_id(db, current_user, request.session_id)
            if not conversation:
                raise HTTPException(
                    status_code=404,
                    detail="Conversación no encontrada o no pertenece al usuario"
                )
            session_id = request.session_id
            print(f"[DEBUG] Using existing conversation: {session_id}")
        else:
            # Crear nueva conversación
            conversation = chat_service.get_or_create_conversation(db, current_user, None)
            session_id = conversation.session_id
            print(f"[DEBUG] Created new conversation: {session_id}")
        
        history = memory_service.get_conversation_history(db, session_id, limit=10)
        print(f"[DEBUG] Retrieved {len(history)} messages from history")
        for i, msg in enumerate(history):
            print(f"[DEBUG] Message {i}: {msg.get('role')} - {msg.get('content', '')[:50]}...")
        
        user_message = chat_service.add_message_to_conversation(
            db, current_user, session_id, "user", request.message
        )
        
        if not user_message:
            raise HTTPException(
                status_code=500,
                detail="Error guardando mensaje del usuario"
            )
        
        print(f"[DEBUG] Saved user message: {user_message.id}")
        
        messages_count = db.query(Message).filter(Message.conversation_id == conversation.id).count()
        print(f"[DEBUG] Total messages in conversation: {messages_count}")
        
        if messages_count == 1:  # Solo el mensaje del usuario
            chat_service.update_conversation_from_first_message(
                db, current_user, session_id, request.message
            )
            print(f"[DEBUG] Updated conversation title from first message")
        
        has_previous_clarification = any(
            "clarification" in msg.get('content', '').lower() or 
            any(keyword in msg.get('content', '').lower() 
                for keyword in ['qué', 'cuál', 'cómo', 'opción'])
            for msg in history if msg.get('role') == 'assistant'
        )
        
        print(f"[DEBUG] Has previous clarification: {has_previous_clarification}")
        
        if has_previous_clarification or len(history) > 1:
            is_ambiguous = False
            print(f"[DEBUG] Skipping ambiguity analysis due to existing context")
        else:
            is_ambiguous = await conversation_service.analyze_ambiguity(request.message)
            print(f"[DEBUG] Ambiguity analysis result: {is_ambiguous}")
        
        if is_ambiguous and not has_previous_clarification:
            # Solo una ronda de clarificación permitida
            clarification_questions = await conversation_service.generate_clarification_questions(request.message)
            
            clarification_content = "[Solicitud de clarificación]"
            clarification_metadata = {"type": "clarification", "questions": len(clarification_questions)}
            
            assistant_message = chat_service.add_message_to_conversation(
                db, current_user, session_id, "assistant", clarification_content, clarification_metadata
            )
            
            print(f"[DEBUG] Generated clarification with {len(clarification_questions)} questions")
            
            response_type = ResponseLevel.CLARIFICATION
            conceptual = None
            accional = None
            tokens_used = 100
            
        else:
            print(f"[DEBUG] Generating strategic response with full context")
            conceptual, accional = await conversation_service.generate_strategic_response(
                request.message, session_id, history_context=history
            )
            
            full_response = f"## Análisis Conceptual\n{conceptual.content}\n\n## Plan de Acción\n{accional.content}"
            response_metadata = {
                "type": "strategic_response",
                "conceptual_confidence": conceptual.confidence,
                "accional_priority": accional.priority,
                "sources": conceptual.sources,
                "context_messages": len(history)
            }
            
            assistant_message = chat_service.add_message_to_conversation(
                db, current_user, session_id, "assistant", full_response, response_metadata
            )
            
            print(f"[DEBUG] Saved assistant response: {assistant_message.id}")
            
            response_type = ResponseLevel.CONCEPTUAL
            clarification_questions = None
            tokens_used = 2000
        
        processing_time = time.time() - start_time
        print(f"[DEBUG] Query processed in {processing_time:.2f}s")
        
        return QueryResponse(
            response_type=response_type,
            session_id=session_id,
            conceptual=conceptual,
            accional=accional,
            clarification=clarification_questions,
            processing_time=processing_time,
            tokens_used=tokens_used,
            model_used=settings.OPENAI_MODEL
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando consulta: {str(e)}"
        )

@router.get("/query/sessions/{session_id}")
async def get_session_history(
    session_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene el historial de conversación de una sesión del usuario autenticado
    """
    
    conversation = chat_service.get_conversation_by_session_id(db, current_user, session_id)
    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversación no encontrada o no pertenece al usuario"
        )
    
    conversation_with_messages = chat_service.get_conversation_with_messages(
        db, current_user, session_id, message_limit=50
    )
    
    if not conversation_with_messages:
        raise HTTPException(
            status_code=404,
            detail="Error obteniendo historial de conversación"
        )
    
    key_info = {}
    if conversation_with_messages.messages:
        # Get the last user message for key info extraction
        last_user_message = None
        for msg in reversed(conversation_with_messages.messages):
            if msg.role == "user":
                last_user_message = msg.content
                break
        
        if last_user_message:
            key_info = memory_service.extract_key_info(db, session_id, last_user_message)
    
    return {
        "session_id": session_id,
        "conversation_id": conversation_with_messages.id,
        "title": conversation_with_messages.title,
        "created_at": conversation_with_messages.created_at,
        "updated_at": conversation_with_messages.updated_at,
        "message_count": conversation_with_messages.message_count,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "metadata": msg.message_metadata
            } for msg in conversation_with_messages.messages
        ],
        "key_information": key_info,
        "context": {"session_id": session_id, "user_id": current_user.id}
    }

@router.delete("/query/sessions/{session_id}")
async def clear_session(
    session_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Elimina una conversación del usuario autenticado
    """
    
    success = chat_service.delete_conversation(db, current_user, session_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Conversación no encontrada o no pertenece al usuario"
        )
    
    # Also clear from in-memory cache if exists
    if session_id in conversation_service.conversation_memory:
        del conversation_service.conversation_memory[session_id]
    
    return {
        "message": f"Conversación {session_id} eliminada exitosamente",
        "success": success,
        "timestamp": datetime.now()
    }

@router.get("/query/memory/status")
async def get_memory_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene el estado del sistema de memoria para el usuario autenticado
    """
    
    try:
        from app.models.conversation import Conversation
        
        user_conversations = db.query(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True
        ).count()
        
        user_messages = db.query(Message).join(Conversation).filter(
            Conversation.user_id == current_user.id,
            Conversation.is_active == True
        ).count()
        
        total_conversations = db.query(Conversation).filter(Conversation.is_active == True).count()
        
        return {
            "status": "connected",
            "database": "postgresql",
            "user_conversations": user_conversations,
            "user_messages": user_messages,
            "total_system_conversations": total_conversations,
            "memory_type": "persistent_with_user_auth",
            "user_id": current_user.id,
            "username": current_user.username,
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "postgresql",
            "error": str(e),
            "memory_type": "fallback_in_memory",
            "user_id": current_user.id,
            "timestamp": datetime.now()
        }
