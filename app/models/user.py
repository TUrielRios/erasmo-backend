"""
Modelos de autenticación y gestión de usuarios
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    """Modelo para usuarios del sistema"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    work_area = Column(String(255), nullable=True)  # Área de desempeño
    role = Column(String(50), default="client")  # 'client' o 'admin'
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    company = relationship("Company", back_populates="users")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    shared_projects = relationship("ProjectShare", foreign_keys="ProjectShare.shared_with_user_id", back_populates="shared_with_user")
    shared_conversations = relationship("ConversationShare", foreign_keys="ConversationShare.shared_with_user_id", back_populates="shared_with_user")
