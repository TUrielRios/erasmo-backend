"""
Modelos de base de datos para proyectos/folders
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.company import Company
    from app.models.conversation import Conversation
    from app.models.project_file import ProjectFile

class Project(Base):
    """
    Modelo para proyectos/folders que agrupan chats, archivos e instrucciones personalizadas.
    Los proyectos mantienen los chats, los archivos y las instrucciones personalizadas en un solo lugar.
    """
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Custom instructions for this project
    custom_instructions = Column(Text, nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="projects")
    company = relationship("Company", back_populates="projects")
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    shared_with = relationship("ProjectShare", back_populates="project", cascade="all, delete-orphan")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")


class ProjectShare(Base):
    """
    Modelo para compartir proyectos con otros usuarios de la misma compañía
    """
    __tablename__ = "project_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    shared_with_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Permissions
    can_edit = Column(Boolean, default=False, nullable=False)  # Can edit project settings
    can_view_chats = Column(Boolean, default=True, nullable=False)  # Can view conversations
    can_create_chats = Column(Boolean, default=False, nullable=False)  # Can create new chats
    
    # Metadata
    shared_at = Column(DateTime(timezone=True), server_default=func.now())
    shared_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="shared_with")
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id], back_populates="shared_projects")
    shared_by_user = relationship("User", foreign_keys=[shared_by_user_id])


class ConversationShare(Base):
    """
    Modelo para compartir conversaciones individuales con otros usuarios de la misma compañía
    """
    __tablename__ = "conversation_shares"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    shared_with_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Permissions
    can_edit = Column(Boolean, default=False, nullable=False)  # Can add messages
    can_view = Column(Boolean, default=True, nullable=False)  # Can view messages
    
    # Metadata
    shared_at = Column(DateTime(timezone=True), server_default=func.now())
    shared_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="shared_with")
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id], back_populates="shared_conversations")
    shared_by_user = relationship("User", foreign_keys=[shared_by_user_id])
