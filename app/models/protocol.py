"""
Modelo de Protocolo reutilizable para múltiples sub-agentes/documentos
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Protocol(Base):
    """Protocolo reutilizable que múltiples documentos pueden referenciar"""
    __tablename__ = "protocols"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Contenido del protocolo
    version = Column(String(50), nullable=False, default="v1")
    category = Column(String(100), nullable=True)  # "ventas", "soporte", etc.
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relación inversa con documentos que usan este protocolo
    company_documents = relationship("CompanyDocument", back_populates="protocol")
