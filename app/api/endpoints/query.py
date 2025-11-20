"""
Endpoints para consultas conversacionales - sin autenticación JWT
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, AsyncGenerator
import time
import uuid
import json
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
from app.models.user import User
from app.models.conversation import Message

router = APIRouter()

# Instancias globales de servicios
conversation_service = ConversationService()
memory_service = MemoryService()
chat_service = ChatService()

@router.post("/query/stream")
async def process_query_stream(
    request: QueryRequest, 
    db: Session = Depends(get_db)
):
    """
    Procesa una consulta con respuesta en streaming (Server-Sent Events)
    """
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generador para streaming de respuestas"""
        start_time = time.time()
        
        try:
            if not request.user_id:
                yield f"data: {json.dumps({'error': 'user_id es requerido en el request'})}\n\n"
                return
            
            # Get user from database
            from app.services.auth_service import AuthService
            current_user = AuthService.get_user_by_id(db, request.user_id)
            if not current_user:
                yield f"data: {json.dumps({'error': 'Usuario no encontrado'})}\n\n"
                return
            
            print(f"[DEBUG] Processing streaming query for user {current_user.id}: {request.message[:50]}...")
            
            # Get or create conversation
            if request.session_id:
                conversation = chat_service.get_conversation_by_session_id(db, current_user, request.session_id)
                if not conversation:
                    yield f"data: {json.dumps({'error': 'Conversación no encontrada'})}\n\n"
                    return
                session_id = request.session_id
            else:
                conversation = chat_service.get_or_create_conversation(db, current_user, None)
                session_id = conversation.session_id
            
            # Send session_id to client
            yield f"data: {json.dumps({'type': 'session_id', 'session_id': session_id})}\n\n"
            
            # Get conversation history
            history = memory_service.get_conversation_history(db, session_id, limit=10)
            
            # Save user message
            user_message = chat_service.add_message_to_conversation(
                db, current_user, session_id, "user", request.message
            )
            
            if not user_message:
                yield f"data: {json.dumps({'error': 'Error guardando mensaje del usuario'})}\n\n"
                return
            
            # Update conversation title if first message
            messages_count = db.query(Message).filter(Message.conversation_id == conversation.id).count()
            if messages_count == 1:
                chat_service.update_conversation_from_first_message(
                    db, current_user, session_id, request.message
                )
            
            # Check for clarification needs
            has_previous_clarification = any(
                "clarification" in msg.get('content', '').lower() or 
                any(keyword in msg.get('content', '').lower() 
                    for keyword in ['qué', 'cuál', 'cómo', 'opción'])
                for msg in history if msg.get('role') == 'assistant'
            )
            
            if has_previous_clarification or len(history) > 1:
                is_ambiguous = False
            else:
                is_ambiguous = await conversation_service.analyze_ambiguity(request.message)
            
            if is_ambiguous and not has_previous_clarification:
                # Handle clarification (non-streaming for simplicity)
                clarification_questions = await conversation_service.generate_clarification_questions(request.message)
                
                clarification_data = {
                    'type': 'clarification',
                    'questions': [q.dict() for q in clarification_questions]
                }
                yield f"data: {json.dumps(clarification_data)}\n\n"
                
                clarification_content = "[Solicitud de clarificación]"
                clarification_metadata = {"type": "clarification", "questions": len(clarification_questions)}
                chat_service.add_message_to_conversation(
                    db, current_user, session_id, "assistant", clarification_content, clarification_metadata
                )
            else:
                # Stream the response
                full_response = ""
                async for chunk in conversation_service.generate_strategic_response_stream(
                    request.message, session_id, current_user.id, 
                    history_context=history,
                    require_analysis=request.require_analysis,
                    attachments=request.attachments  # Pass attachments
                ):
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                
                # Save complete response to database
                try:
                    memory_service.add_message(db, session_id, "assistant", full_response)
                    print(f"✅ [DEBUG] Streaming response saved to memory")
                except Exception as e:
                    print(f"❌ [DEBUG] Error saving streaming response: {e}")
            
            # Send completion signal
            processing_time = time.time() - start_time
            completion_data = {
                'type': 'done',
                'processing_time': processing_time,
                'model_used': settings.OPENAI_MODEL
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
        except Exception as e:
            print(f"[ERROR] Error in streaming query: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest, 
    db: Session = Depends(get_db)
):
    """
    Procesa una consulta sin autenticación JWT - requiere user_id en el request
    """
    
    start_time = time.time()
    
    try:
        if not request.user_id:
            raise HTTPException(
                status_code=400,
                detail="user_id es requerido en el request"
            )
        
        # Get user from database
        from app.services.auth_service import AuthService
        current_user = AuthService.get_user_by_id(db, request.user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
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
            tokens_used = 500
            
        else:
            print(f"[DEBUG] Generating strategic response with full context")
            if request.require_analysis:
                # Generate structured analysis and action plan
                try:
                    conceptual, accional = await conversation_service.generate_strategic_response(
                        request.message, session_id, current_user.id, 
                        history_context=history,
                        require_analysis=True,
                        attachments=request.attachments  # Pass attachments
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
                    accional = await conversation_service.generate_strategic_response(
                        request.message, session_id, current_user.id, 
                        history_context=history,
                        require_analysis=True,
                        attachments=request.attachments  # Pass attachments
                    )[1]  # Get accional from tuple
                    print(f"✅ [DEBUG] Accional response generated with instructions")
                except Exception as e:
                    print(f"❌ [DEBUG] Error generating accional response: {e}")
                    accional = AccionalResponse(
                        content="Error generando plan de acción. Intenta nuevamente.",
                        priority="media",
                        timeline="Indefinido"
                    )

                # Save assistant response with structured format
                try:
                    full_response = f"## Análisis Conceptual\n{conceptual.content}\n\n## Plan de Acción\n{accional.content}"
                    memory_service.add_message(db, session_id, "assistant", full_response)
                    print(f"✅ [DEBUG] Assistant response added to memory")
                except Exception as e:
                    print(f"❌ [DEBUG] Error adding assistant response to memory: {e}")
                    
                response_metadata = {
                    "type": "strategic_response",
                    "conceptual_confidence": conceptual.confidence,
                    "accional_priority": accional.priority,
                    "sources": conceptual.sources,
                    "context_messages": len(history),
                    "require_analysis": True
                }
                
                response_type = ResponseLevel.CONCEPTUAL
                    
            else:
                try:
                    conceptual, accional = await conversation_service.generate_strategic_response(
                        request.message, session_id, current_user.id, 
                        history_context=history,
                        require_analysis=False,
                        attachments=request.attachments  # Pass attachments
                    )
                    
                    # For normal responses, conceptual.content has the full response
                    normal_response = conceptual.content
                    print(f"✅ [DEBUG] Normal response generated")
                    
                    # Save assistant response as plain text
                    try:
                        memory_service.add_message(db, session_id, "assistant", normal_response)
                        print(f"✅ [DEBUG] Normal assistant response added to memory")
                    except Exception as e:
                        print(f"❌ [DEBUG] Error adding assistant response to memory: {e}")
                        
                    response_metadata = {
                        "type": "normal_response",
                        "sources": conceptual.sources,
                        "context_messages": len(history),
                        "require_analysis": False
                    }
                    
                    response_type = ResponseLevel.NORMAL
                    
                    # Instead, put the response in a simple format
                    conceptual = ConceptualResponse(
                        content=normal_response,
                        sources=conceptual.sources,
                        confidence=conceptual.confidence
                    )
                    accional = None
                    
                except Exception as e:
                    print(f"❌ [DEBUG] Error generating normal response: {e}")
                    conceptual = ConceptualResponse(
                        content="Error generando respuesta. Intenta nuevamente.",
                        sources=[],
                        confidence=0.1
                    )
                    accional = None
                    response_type = ResponseLevel.NORMAL
                    response_metadata = {
                        "type": "error",
                        "require_analysis": False
                    }

            assistant_message = chat_service.add_message_to_conversation(
                db, current_user, session_id, "assistant", 
                conceptual.content, 
                response_metadata
            )
            
            print(f"[DEBUG] Saved assistant response: {assistant_message.id}")
            
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
    user_id: int,  # Now requires user_id as parameter
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de conversación - requiere user_id
    """
    
    # Get user from database
    from app.services.auth_service import AuthService
    current_user = AuthService.get_user_by_id(db, user_id)
    if not current_user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )
    
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
        "context": {"session_id": session_id, "user_id": user_id}
    }

@router.delete("/query/sessions/{session_id}")
async def clear_session(
    session_id: str, 
    user_id: int,  # Now requires user_id as parameter
    db: Session = Depends(get_db)
):
    """
    Elimina una conversación - requiere user_id
    """
    
    # Get user from database
    from app.services.auth_service import AuthService
    current_user = AuthService.get_user_by_id(db, user_id)
    if not current_user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )
    
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
    user_id: int,  # Now requires user_id as parameter
    db: Session = Depends(get_db)
):
    """
    Obtiene el estado del sistema de memoria - requiere user_id
    """
    
    # Get user from database
    from app.services.auth_service import AuthService
    current_user = AuthService.get_user_by_id(db, user_id)
    if not current_user:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )
    
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
            "user_id": user_id,
            "timestamp": datetime.now()
        }
