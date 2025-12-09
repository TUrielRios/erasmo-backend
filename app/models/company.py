"""
Modelos de base de datos para compañías y documentos
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from app.models.schemas import DocumentCategory
import enum

class Company(Base):
    """Modelo de compañía"""
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    industry = Column(String(255), nullable=False)
    sector = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    users = relationship("User", back_populates="company")
    documents = relationship("CompanyDocument", back_populates="company", cascade="all, delete-orphan")
    ai_configurations = relationship("AIConfiguration", back_populates="company", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="company", cascade="all, delete-orphan")

class CompanyDocument(Base):
    """Modelo de documento de compañía"""
    __tablename__ = "company_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    category = Column(SQLEnum(DocumentCategory), nullable=False, default=DocumentCategory.KNOWLEDGE_BASE)
    description = Column(Text, nullable=True)
    priority = Column(Integer, nullable=False, default=0)  # 1=highest, 5=lowest
    processing_status = Column(String(50), nullable=False, default="pending")
    processed_chunks = Column(Integer, nullable=False, default=0)
    total_chunks = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Campos para soporte de protocolos centralizados
    protocol_id = Column(Integer, ForeignKey("protocols.id", ondelete="SET NULL"), nullable=True)
    use_protocol = Column(Boolean, default=False, nullable=False)
    
    # Relaciones
    company = relationship("Company", back_populates="documents")
    protocol = relationship("Protocol", back_populates="company_documents")

class AIConfiguration(Base):
    """Modelo de configuración de IA por compañía"""
    __tablename__ = "ai_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, unique=True)
    methodology_prompt = Column(Text, nullable=True)
    knowledge_base = Column(Text, nullable=True)  # JSON string
    personality_traits = Column(Text, nullable=True)  # JSON string
    response_style = Column(String(100), nullable=False, default="professional")
    model_name = Column(String(100), nullable=False, default="gpt-4")
    temperature = Column(String(10), nullable=False, default="0.7")
    max_tokens = Column(Integer, nullable=False, default=2000)
    instruction_priority = Column(String(20), nullable=False, default="high")
    knowledge_base_priority = Column(String(20), nullable=False, default="high")
    fallback_to_general = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    company = relationship("Company", back_populates="ai_configurations")
