from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base

class FileCategory(str, enum.Enum):
    """Categorias de archivos de proyecto"""
    INSTRUCTIONS = "instructions"
    KNOWLEDGE_BASE = "knowledge_base"
    REFERENCE = "reference"
    GENERAL = "general"

class ProcessingStatus(str, enum.Enum):
    """Estados de procesamiento de archivos"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProjectFile(Base):
    """Modelo para archivos asociados a proyectos"""
    __tablename__ = "project_files"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)
    category = Column(SQLEnum(FileCategory), nullable=False, default=FileCategory.GENERAL)
    
    # Procesamiento
    processing_status = Column(SQLEnum(ProcessingStatus), nullable=False, default=ProcessingStatus.PENDING)
    processed_chunks = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Metadatos
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=5)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relaciones
    project = relationship("Project", back_populates="files")
    
    def __repr__(self):
        return f"<ProjectFile(id={self.id}, filename={self.filename}, project_id={self.project_id})>"
