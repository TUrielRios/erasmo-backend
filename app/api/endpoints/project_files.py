"""
Endpoints para gestion de archivos de proyectos
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.models.schemas import (
    ProjectFileResponse, 
    ProjectFileUpdate,
    FileCategory
)
from app.services.project_file_service import ProjectFileService
from app.services.project_service import ProjectService

router = APIRouter()

@router.post("/projects/{project_id}/files", response_model=ProjectFileResponse)
async def upload_project_file(
    project_id: int,
    user_id: int,
    file: UploadFile = File(...),
    category: FileCategory = Form(FileCategory.GENERAL),
    description: Optional[str] = Form(None),
    priority: int = Form(5),
    db: Session = Depends(get_db)
):
    """
    Sube un archivo a un proyecto
    
    Args:
        project_id: ID del proyecto
        user_id: ID del usuario
        file: Archivo a subir (.txt, .md)
        category: Categoria del archivo (instructions, knowledge_base, reference, general)
        description: Descripcion opcional del archivo
        priority: Prioridad del archivo (1-10, 1=mas alta)
    """
    
    # Verificar que el proyecto existe y el usuario tiene acceso
    project = ProjectService.get_project_by_id(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    try:
        db_file = await ProjectFileService.upload_file(
            db, project_id, file, category, description, priority
        )
        
        return ProjectFileResponse(
            id=db_file.id,
            project_id=db_file.project_id,
            filename=db_file.filename,
            original_filename=db_file.original_filename,
            file_size=db_file.file_size,
            file_type=db_file.file_type,
            category=db_file.category.value,
            processing_status=db_file.processing_status.value,
            processed_chunks=db_file.processed_chunks,
            total_chunks=db_file.total_chunks,
            description=db_file.description,
            priority=db_file.priority,
            created_at=db_file.created_at,
            processed_at=db_file.processed_at,
            is_active=db_file.is_active,
            error_message=db_file.error_message
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {str(e)}")

@router.get("/projects/{project_id}/files", response_model=List[ProjectFileResponse])
def get_project_files(
    project_id: int,
    user_id: int,
    category: Optional[FileCategory] = None,
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los archivos de un proyecto
    
    Args:
        project_id: ID del proyecto
        user_id: ID del usuario
        category: Filtrar por categoria (opcional)
    """
    
    # Verificar acceso al proyecto
    project = ProjectService.get_project_by_id(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    files = ProjectFileService.get_project_files(db, project_id, category)
    
    return [
        ProjectFileResponse(
            id=f.id,
            project_id=f.project_id,
            filename=f.filename,
            original_filename=f.original_filename,
            file_size=f.file_size,
            file_type=f.file_type,
            category=f.category.value,
            processing_status=f.processing_status.value,
            processed_chunks=f.processed_chunks,
            total_chunks=f.total_chunks,
            description=f.description,
            priority=f.priority,
            created_at=f.created_at,
            processed_at=f.processed_at,
            is_active=f.is_active,
            error_message=f.error_message
        )
        for f in files
    ]

@router.get("/projects/{project_id}/files/{file_id}", response_model=ProjectFileResponse)
def get_project_file(
    project_id: int,
    file_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene un archivo especifico de un proyecto"""
    
    # Verificar acceso al proyecto
    project = ProjectService.get_project_by_id(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    db_file = ProjectFileService.get_file_by_id(db, file_id)
    if not db_file or db_file.project_id != project_id:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return ProjectFileResponse(
        id=db_file.id,
        project_id=db_file.project_id,
        filename=db_file.filename,
        original_filename=db_file.original_filename,
        file_size=db_file.file_size,
        file_type=db_file.file_type,
        category=db_file.category.value,
        processing_status=db_file.processing_status.value,
        processed_chunks=db_file.processed_chunks,
        total_chunks=db_file.total_chunks,
        description=db_file.description,
        priority=db_file.priority,
        created_at=db_file.created_at,
        processed_at=db_file.processed_at,
        is_active=db_file.is_active,
        error_message=db_file.error_message
    )

@router.get("/projects/{project_id}/files/{file_id}/content")
def get_project_file_content(
    project_id: int,
    file_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene el contenido de un archivo"""
    
    # Verificar acceso al proyecto
    project = ProjectService.get_project_by_id(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    content = ProjectFileService.get_file_content(db, file_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Archivo no encontrado o no se pudo leer")
    
    return {"content": content}

@router.put("/projects/{project_id}/files/{file_id}", response_model=ProjectFileResponse)
def update_project_file(
    project_id: int,
    file_id: int,
    user_id: int,
    update_data: ProjectFileUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza los metadatos de un archivo"""
    
    # Verificar acceso al proyecto
    project = ProjectService.get_project_by_id(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    db_file = ProjectFileService.update_file(db, file_id, update_data)
    if not db_file:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return ProjectFileResponse(
        id=db_file.id,
        project_id=db_file.project_id,
        filename=db_file.filename,
        original_filename=db_file.original_filename,
        file_size=db_file.file_size,
        file_type=db_file.file_type,
        category=db_file.category.value,
        processing_status=db_file.processing_status.value,
        processed_chunks=db_file.processed_chunks,
        total_chunks=db_file.total_chunks,
        description=db_file.description,
        priority=db_file.priority,
        created_at=db_file.created_at,
        processed_at=db_file.processed_at,
        is_active=db_file.is_active,
        error_message=db_file.error_message
    )

@router.delete("/projects/{project_id}/files/{file_id}")
def delete_project_file(
    project_id: int,
    file_id: int,
    user_id: int,
    permanent: bool = False,
    db: Session = Depends(get_db)
):
    """
    Elimina un archivo de un proyecto
    
    Args:
        permanent: Si es True, elimina permanentemente. Si es False, solo desactiva (soft delete)
    """
    
    # Verificar acceso al proyecto
    project = ProjectService.get_project_by_id(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if permanent:
        success = ProjectFileService.delete_file_permanently(db, file_id)
    else:
        success = ProjectFileService.delete_file(db, file_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return {
        "success": True,
        "message": "Archivo eliminado permanentemente" if permanent else "Archivo desactivado"
    }

@router.get("/projects/{project_id}/files/stats")
def get_project_file_stats(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene estadisticas de archivos del proyecto"""
    
    # Verificar acceso al proyecto
    project = ProjectService.get_project_by_id(db, project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    stats = ProjectFileService.get_project_file_stats(db, project_id)
    
    return stats
