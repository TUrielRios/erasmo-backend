"""
Endpoints para gestión de proyectos/folders
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.services.project_service import ProjectService
from app.services.auth_service import AuthService
from app.models.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectShareCreate,
    ProjectShareResponse,
    ConversationShareCreate,
    ConversationShareResponse
)

router = APIRouter(prefix="/projects", tags=["projects"])
project_service = ProjectService()

@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Crear nuevo proyecto/folder"""
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        project = project_service.create_project(db, current_user, project_data)
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            user_id=project.user_id,
            company_id=project.company_id,
            custom_instructions=project.custom_instructions,
            is_active=project.is_active,
            created_at=project.created_at,
            updated_at=project.updated_at,
            conversation_count=0
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando proyecto: {str(e)}")

@router.get("", response_model=List[ProjectResponse])
async def get_user_projects(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_shared: bool = Query(True, description="Incluir proyectos compartidos"),
    db: Session = Depends(get_db)
):
    """Obtener todos los proyectos del usuario (propios y compartidos)"""
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        projects = project_service.get_user_projects(db, current_user, skip, limit, include_shared)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo proyectos: {str(e)}")

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Obtener proyecto por ID"""
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        project = project_service.get_project_by_id(db, current_user, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        from app.models.conversation import Conversation
        conversation_count = db.query(Conversation).filter(
            Conversation.project_id == project.id,
            Conversation.is_active == True
        ).count()
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            user_id=project.user_id,
            company_id=project.company_id,
            custom_instructions=project.custom_instructions,
            is_active=project.is_active,
            created_at=project.created_at,
            updated_at=project.updated_at,
            conversation_count=conversation_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo proyecto: {str(e)}")

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Actualizar proyecto"""
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        project = project_service.update_project(db, current_user, project_id, project_data)
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        from app.models.conversation import Conversation
        conversation_count = db.query(Conversation).filter(
            Conversation.project_id == project.id,
            Conversation.is_active == True
        ).count()
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            user_id=project.user_id,
            company_id=project.company_id,
            custom_instructions=project.custom_instructions,
            is_active=project.is_active,
            created_at=project.created_at,
            updated_at=project.updated_at,
            conversation_count=conversation_count
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando proyecto: {str(e)}")

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar proyecto"""
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        success = project_service.delete_project(db, current_user, project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        return {"message": "Proyecto eliminado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando proyecto: {str(e)}")

@router.post("/{project_id}/share", response_model=ProjectShareResponse)
async def share_project(
    project_id: int,
    share_data: ProjectShareCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Compartir proyecto con otro usuario de la misma compañía"""
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        share = project_service.share_project(db, current_user, project_id, share_data)
        
        return ProjectShareResponse(
            id=share.id,
            project_id=share.project_id,
            shared_with_user_id=share.shared_with_user_id,
            can_edit=share.can_edit,
            can_view_chats=share.can_view_chats,
            can_create_chats=share.can_create_chats,
            shared_at=share.shared_at,
            shared_by_user_id=share.shared_by_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error compartiendo proyecto: {str(e)}")

@router.delete("/{project_id}/share/{user_id_to_unshare}")
async def unshare_project(
    project_id: int,
    user_id_to_unshare: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Dejar de compartir proyecto con un usuario"""
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        success = project_service.unshare_project(db, current_user, project_id, user_id_to_unshare)
        if not success:
            raise HTTPException(status_code=404, detail="Proyecto o compartido no encontrado")
        
        return {"message": "Proyecto dejado de compartir exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/{project_id}/shares", response_model=List[ProjectShareResponse])
async def get_project_shares(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Obtener lista de usuarios con quienes se ha compartido el proyecto"""
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        shares = project_service.get_project_shares(db, current_user, project_id)
        return shares
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo compartidos: {str(e)}")

@router.post("/conversations/{session_id}/share", response_model=ConversationShareResponse)
async def share_conversation(
    session_id: str,  # Cambiado de int a str para aceptar UUID
    share_data: ConversationShareCreate,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Compartir conversación con otro usuario de la misma compañía (usando session_id)"""
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Buscar la conversación por session_id en lugar de id
        from app.models.conversation import Conversation
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        
        # Usar el ID numérico de la conversación para el servicio
        share = project_service.share_conversation(db, current_user, conversation.id, share_data)
        
        return ConversationShareResponse(
            id=share.id,
            conversation_id=share.conversation_id,
            shared_with_user_id=share.shared_with_user_id,
            can_edit=share.can_edit,
            can_view=share.can_view,
            shared_at=share.shared_at,
            shared_by_user_id=share.shared_by_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error compartiendo conversación: {str(e)}")

@router.delete("/conversations/{session_id}/share/{user_id_to_unshare}")
async def unshare_conversation(
    session_id: str,  # Cambiado de int a str para aceptar UUID
    user_id_to_unshare: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Dejar de compartir conversación con un usuario (usando session_id)"""
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Buscar la conversación por session_id
        from app.models.conversation import Conversation
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        
        success = project_service.unshare_conversation(db, current_user, conversation.id, user_id_to_unshare)
        if not success:
            raise HTTPException(status_code=404, detail="Conversación o compartido no encontrado")
        
        return {"message": "Conversación dejada de compartir exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/conversations/{session_id}/shares", response_model=List[ConversationShareResponse])
async def get_conversation_shares(
    session_id: str,  # Cambiado de int a str para aceptar UUID
    user_id: int,
    db: Session = Depends(get_db)
):
    """Obtener lista de usuarios con quienes se ha compartido la conversación (usando session_id)"""
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Buscar la conversación por session_id
        from app.models.conversation import Conversation
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        
        shares = project_service.get_conversation_shares(db, current_user, conversation.id)
        return shares
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo compartidos: {str(e)}")