"""
Servicio para gestión de archivos de proyectos
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
import os
import hashlib
from datetime import datetime

from app.models.project_file import ProjectFile, FileCategory, ProcessingStatus
from app.models.schemas import ProjectFileResponse, ProjectFileUpdate
from app.services.ingestion_service import IngestionService
from app.core.config import settings

class ProjectFileService:
    """Servicio para gestionar archivos de proyectos"""
    
    @staticmethod
    def get_project_storage_path(project_id: int) -> str:
        """Obtiene la ruta de almacenamiento para un proyecto"""
        base_path = "documents/projects"
        project_path = os.path.join(base_path, f"project_{project_id}")
        os.makedirs(project_path, exist_ok=True)
        return project_path
    
    @staticmethod
    async def upload_file(
        db: Session,
        project_id: int,
        file: UploadFile,
        category: FileCategory,
        description: Optional[str] = None,
        priority: int = 5
    ) -> ProjectFile:
        """
        Sube un archivo a un proyecto
        """
        
        # Validar tipo de archivo
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise ValueError(f"Tipo de archivo no soportado: {file_extension}")
        
        # Leer contenido
        content = await file.read()
        file_size = len(content)
        
        # Validar tamaño
        if file_size > settings.MAX_FILE_SIZE:
            raise ValueError(f"Archivo demasiado grande. Máximo: {settings.MAX_FILE_SIZE} bytes")
        
        # Generar nombre único
        file_hash = hashlib.md5(f"{file.filename}{datetime.utcnow()}".encode()).hexdigest()[:8]
        unique_filename = f"{file_hash}_{file.filename}"
        
        # Guardar archivo
        storage_path = ProjectFileService.get_project_storage_path(project_id)
        file_path = os.path.join(storage_path, unique_filename)
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Crear registro en BD
        db_file = ProjectFile(
            project_id=project_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_extension,
            category=category,
            description=description,
            priority=priority,
            processing_status=ProcessingStatus.PENDING
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        # Procesar archivo en background
        try:
            await ProjectFileService._process_file(db, db_file, content)
        except Exception as e:
            print(f"Error procesando archivo {file.filename}: {e}")
            db_file.processing_status = ProcessingStatus.FAILED
            db_file.error_message = str(e)
            db.commit()
        
        return db_file
    
    @staticmethod
    async def _process_file(db: Session, db_file: ProjectFile, content: bytes):
        """
        Procesa un archivo y lo indexa en la base vectorial
        """
        
        # Actualizar estado
        db_file.processing_status = ProcessingStatus.PROCESSING
        db.commit()
        
        ingestion_service = IngestionService()
        
        # Metadatos para el archivo
        metadata = {
            "project_id": db_file.project_id,
            "file_id": db_file.id,
            "category": db_file.category.value,
            "priority": db_file.priority,
            "source": "project_file"
        }
        
        # Procesar según categoría
        if db_file.category == FileCategory.INSTRUCTIONS:
            chunk_ids = await ingestion_service.process_personality_file(
                content, db_file.original_filename, metadata
            )
        else:
            chunk_ids = await ingestion_service.process_knowledge_file(
                content, db_file.original_filename, metadata
            )
        
        # Actualizar estado
        db_file.processing_status = ProcessingStatus.COMPLETED
        db_file.processed_chunks = len(chunk_ids)
        db_file.total_chunks = len(chunk_ids)
        db_file.processed_at = datetime.utcnow()
        db.commit()
        
        print(f"✅ Archivo {db_file.original_filename} procesado: {len(chunk_ids)} chunks")
    
    @staticmethod
    def get_project_files(
        db: Session,
        project_id: int,
        category: Optional[FileCategory] = None,
        active_only: bool = True
    ) -> List[ProjectFile]:
        """
        Obtiene los archivos de un proyecto
        """
        query = db.query(ProjectFile).filter(ProjectFile.project_id == project_id)
        
        if category:
            query = query.filter(ProjectFile.category == category)
        
        if active_only:
            query = query.filter(ProjectFile.is_active == True)
        
        return query.order_by(ProjectFile.priority.asc(), ProjectFile.created_at.desc()).all()
    
    @staticmethod
    def get_file_by_id(db: Session, file_id: int) -> Optional[ProjectFile]:
        """Obtiene un archivo por ID"""
        return db.query(ProjectFile).filter(ProjectFile.id == file_id).first()
    
    @staticmethod
    def update_file(
        db: Session,
        file_id: int,
        update_data: ProjectFileUpdate
    ) -> Optional[ProjectFile]:
        """
        Actualiza un archivo de proyecto
        """
        db_file = ProjectFileService.get_file_by_id(db, file_id)
        if not db_file:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_file, key, value)
        
        db_file.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_file)
        
        return db_file
    
    @staticmethod
    def delete_file(db: Session, file_id: int) -> bool:
        """
        Elimina un archivo de proyecto (soft delete)
        """
        db_file = ProjectFileService.get_file_by_id(db, file_id)
        if not db_file:
            return False
        
        db_file.is_active = False
        db.commit()
        
        return True
    
    @staticmethod
    def delete_file_permanently(db: Session, file_id: int) -> bool:
        """
        Elimina un archivo de proyecto permanentemente
        """
        db_file = ProjectFileService.get_file_by_id(db, file_id)
        if not db_file:
            return False
        
        # Eliminar archivo físico
        try:
            if os.path.exists(db_file.file_path):
                os.remove(db_file.file_path)
        except Exception as e:
            print(f"Error eliminando archivo físico: {e}")
        
        # Eliminar de BD
        db.delete(db_file)
        db.commit()
        
        return True
    
    @staticmethod
    def get_file_content(db: Session, file_id: int) -> Optional[str]:
        """
        Obtiene el contenido de un archivo
        """
        db_file = ProjectFileService.get_file_by_id(db, file_id)
        if not db_file or not os.path.exists(db_file.file_path):
            return None
        
        try:
            with open(db_file.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error leyendo archivo: {e}")
            return None
    
    @staticmethod
    def get_project_instructions(db: Session, project_id: int) -> str:
        """
        Obtiene todas las instrucciones de un proyecto concatenadas
        """
        instruction_files = ProjectFileService.get_project_files(
            db, project_id, category=FileCategory.INSTRUCTIONS
        )
        
        instructions = []
        for file in instruction_files:
            content = ProjectFileService.get_file_content(db, file.id)
            if content:
                instructions.append(f"# {file.original_filename}\n\n{content}")
        
        return "\n\n---\n\n".join(instructions)
    
    @staticmethod
    def get_project_file_stats(db: Session, project_id: int) -> Dict[str, Any]:
        """
        Obtiene estadísticas de archivos de un proyecto
        """
        files = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id,
            ProjectFile.is_active == True
        ).all()
        
        stats = {
            "total_files": len(files),
            "by_category": {},
            "by_status": {},
            "total_size": sum(f.file_size for f in files),
            "total_chunks": sum(f.processed_chunks for f in files)
        }
        
        for file in files:
            # Por categoría
            category = file.category.value
            if category not in stats["by_category"]:
                stats["by_category"][category] = 0
            stats["by_category"][category] += 1
            
            # Por estado
            status = file.processing_status.value
            if status not in stats["by_status"]:
                stats["by_status"][status] = 0
            stats["by_status"][status] += 1
        
        return stats
