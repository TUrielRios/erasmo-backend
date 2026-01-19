"""
Servicio para gestion de proyectos/folders
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime

from app.models.user import User
from app.models.project import Project, ProjectShare, ConversationShare
from app.models.conversation import Conversation
from app.models.schemas import (
    ProjectCreate, 
    ProjectUpdate, 
    ProjectResponse,
    ProjectShareCreate,
    ProjectShareResponse,
    ConversationShareCreate,
    ConversationShareResponse
)

class ProjectService:
    """Servicio para gestion de proyectos/folders"""
    
    @staticmethod
    def create_project(db: Session, user: User, project_data: ProjectCreate) -> Project:
        """Crear un nuevo proyecto"""
        
        if not user.company_id:
            raise ValueError("El usuario debe pertenecer a una compania para crear proyectos")
        
        db_project = Project(
            name=project_data.name,
            description=project_data.description,
            custom_instructions=project_data.custom_instructions,
            user_id=user.id,
            company_id=user.company_id,
            is_active=True
        )
        
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        return db_project
    
    @staticmethod
    def get_user_projects(
        db: Session, 
        user: User, 
        skip: int = 0, 
        limit: int = 50,
        include_shared: bool = True
    ) -> List[ProjectResponse]:
        """Obtener todos los proyectos del usuario (propios y compartidos)"""
        
        # Proyectos propios
        own_projects_query = db.query(Project).filter(
            Project.user_id == user.id,
            Project.is_active == True
        )
        
        if include_shared:
            # Proyectos compartidos con el usuario
            shared_project_ids = db.query(ProjectShare.project_id).filter(
                ProjectShare.shared_with_user_id == user.id
            ).subquery()
            
            shared_projects_query = db.query(Project).filter(
                Project.id.in_(shared_project_ids),
                Project.is_active == True
            )
            
            # Combinar ambas consultas
            projects = own_projects_query.union(shared_projects_query).order_by(
                desc(Project.updated_at)
            ).offset(skip).limit(limit).all()
        else:
            projects = own_projects_query.order_by(
                desc(Project.updated_at)
            ).offset(skip).limit(limit).all()
        
        # Convertir a response con conteo de conversaciones
        result = []
        for project in projects:
            conversation_count = db.query(Conversation).filter(
                Conversation.project_id == project.id,
                Conversation.is_active == True
            ).count()
            
            project_response = ProjectResponse(
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
            result.append(project_response)
        
        return result
    
    @staticmethod
    def get_project_by_id(db: Session, project_id: int, user_id: int) -> Optional[Project]:
        """Obtener proyecto por ID verificando permisos"""
        
        # Verificar si es el dueno
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user_id,
            Project.is_active == True
        ).first()
        
        if project:
            return project
        
        # Verificar si esta compartido con el usuario
        shared = db.query(ProjectShare).filter(
            ProjectShare.project_id == project_id,
            ProjectShare.shared_with_user_id == user_id
        ).first()
        
        if shared:
            return db.query(Project).filter(
                Project.id == project_id,
                Project.is_active == True
            ).first()
        
        return None
    
    @staticmethod
    def update_project(
        db: Session, 
        user: User, 
        project_id: int, 
        project_data: ProjectUpdate
    ) -> Optional[Project]:
        """Actualizar proyecto"""
        
        project = ProjectService.get_project_by_id(db, project_id, user.id)
        if not project:
            return None
        
        # Verificar si tiene permisos de edicion
        if project.user_id != user.id:
            # Verificar si tiene permisos de edicion compartidos
            share = db.query(ProjectShare).filter(
                ProjectShare.project_id == project_id,
                ProjectShare.shared_with_user_id == user.id,
                ProjectShare.can_edit == True
            ).first()
            
            if not share:
                raise PermissionError("No tienes permisos para editar este proyecto")
        
        # Actualizar campos
        if project_data.name is not None:
            project.name = project_data.name
        if project_data.description is not None:
            project.description = project_data.description
        if project_data.custom_instructions is not None:
            project.custom_instructions = project_data.custom_instructions
        if project_data.is_active is not None:
            project.is_active = project_data.is_active
        
        project.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(project)
        
        return project
    
    @staticmethod
    def delete_project(db: Session, user: User, project_id: int) -> bool:
        """Eliminar proyecto (soft delete)"""
        
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user.id,
            Project.is_active == True
        ).first()
        
        if not project:
            return False
        
        project.is_active = False
        project.updated_at = datetime.utcnow()
        
        db.commit()
        return True
    
    @staticmethod
    def share_project(
        db: Session, 
        user: User, 
        project_id: int, 
        share_data: ProjectShareCreate
    ) -> ProjectShare:
        """Compartir proyecto con otro usuario de la misma compania"""
        
        # Verificar que el proyecto existe y pertenece al usuario
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user.id,
            Project.is_active == True
        ).first()
        
        if not project:
            raise ValueError("Proyecto no encontrado o no tienes permisos")
        
        # Verificar que el usuario con quien se comparte existe y es de la misma compania
        target_user = db.query(User).filter(
            User.id == share_data.shared_with_user_id,
            User.company_id == user.company_id,
            User.is_active == True
        ).first()
        
        if not target_user:
            raise ValueError("Usuario no encontrado o no pertenece a la misma compania")
        
        # Verificar si ya esta compartido
        existing_share = db.query(ProjectShare).filter(
            ProjectShare.project_id == project_id,
            ProjectShare.shared_with_user_id == share_data.shared_with_user_id
        ).first()
        
        if existing_share:
            # Actualizar permisos
            existing_share.can_edit = share_data.can_edit
            existing_share.can_view_chats = share_data.can_view_chats
            existing_share.can_create_chats = share_data.can_create_chats
            db.commit()
            db.refresh(existing_share)
            return existing_share
        
        # Crear nuevo share
        db_share = ProjectShare(
            project_id=project_id,
            shared_with_user_id=share_data.shared_with_user_id,
            can_edit=share_data.can_edit,
            can_view_chats=share_data.can_view_chats,
            can_create_chats=share_data.can_create_chats,
            shared_by_user_id=user.id
        )
        
        db.add(db_share)
        db.commit()
        db.refresh(db_share)
        
        return db_share
    
    @staticmethod
    def unshare_project(db: Session, user: User, project_id: int, user_id_to_unshare: int) -> bool:
        """Dejar de compartir proyecto con un usuario"""
        
        # Verificar que el proyecto pertenece al usuario
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user.id,
            Project.is_active == True
        ).first()
        
        if not project:
            return False
        
        # Eliminar el share
        share = db.query(ProjectShare).filter(
            ProjectShare.project_id == project_id,
            ProjectShare.shared_with_user_id == user_id_to_unshare
        ).first()
        
        if share:
            db.delete(share)
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def get_project_shares(db: Session, user: User, project_id: int) -> List[ProjectShareResponse]:
        """Obtener lista de usuarios con quienes se ha compartido el proyecto"""
        
        # Verificar que el proyecto pertenece al usuario
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user.id,
            Project.is_active == True
        ).first()
        
        if not project:
            return []
        
        shares = db.query(ProjectShare).filter(
            ProjectShare.project_id == project_id
        ).all()
        
        return [
            ProjectShareResponse(
                id=share.id,
                project_id=share.project_id,
                shared_with_user_id=share.shared_with_user_id,
                can_edit=share.can_edit,
                can_view_chats=share.can_view_chats,
                can_create_chats=share.can_create_chats,
                shared_at=share.shared_at,
                shared_by_user_id=share.shared_by_user_id
            ) for share in shares
        ]
    
    @staticmethod
    def share_conversation(
        db: Session, 
        user: User, 
        conversation_id: int, 
        share_data: ConversationShareCreate
    ) -> ConversationShare:
        """Compartir conversacion con otro usuario de la misma compania"""
        
        # Verificar que la conversacion existe y pertenece al usuario
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
            Conversation.is_active == True
        ).first()
        
        if not conversation:
            raise ValueError("Conversacion no encontrada o no tienes permisos")
        
        # Verificar que el usuario con quien se comparte existe y es de la misma compania
        target_user = db.query(User).filter(
            User.id == share_data.shared_with_user_id,
            User.company_id == user.company_id,
            User.is_active == True
        ).first()
        
        if not target_user:
            raise ValueError("Usuario no encontrado o no pertenece a la misma compania")
        
        # Verificar si ya esta compartido
        existing_share = db.query(ConversationShare).filter(
            ConversationShare.conversation_id == conversation_id,
            ConversationShare.shared_with_user_id == share_data.shared_with_user_id
        ).first()
        
        if existing_share:
            # Actualizar permisos
            existing_share.can_edit = share_data.can_edit
            existing_share.can_view = share_data.can_view
            db.commit()
            db.refresh(existing_share)
            return existing_share
        
        # Crear nuevo share
        db_share = ConversationShare(
            conversation_id=conversation_id,
            shared_with_user_id=share_data.shared_with_user_id,
            can_edit=share_data.can_edit,
            can_view=share_data.can_view,
            shared_by_user_id=user.id
        )
        
        db.add(db_share)
        db.commit()
        db.refresh(db_share)
        
        return db_share
    
    @staticmethod
    def unshare_conversation(db: Session, user: User, conversation_id: int, user_id_to_unshare: int) -> bool:
        """Dejar de compartir conversacion con un usuario"""
        
        # Verificar que la conversacion pertenece al usuario
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
            Conversation.is_active == True
        ).first()
        
        if not conversation:
            return False
        
        # Eliminar el share
        share = db.query(ConversationShare).filter(
            ConversationShare.conversation_id == conversation_id,
            ConversationShare.shared_with_user_id == user_id_to_unshare
        ).first()
        
        if share:
            db.delete(share)
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def get_conversation_shares(db: Session, user: User, conversation_id: int) -> List[ConversationShareResponse]:
        """Obtener lista de usuarios con quienes se ha compartido la conversacion"""
        
        # Verificar que la conversacion pertenece al usuario
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
            Conversation.is_active == True
        ).first()
        
        if not conversation:
            return []
        
        shares = db.query(ConversationShare).filter(
            ConversationShare.conversation_id == conversation_id
        ).all()
        
        return [
            ConversationShareResponse(
                id=share.id,
                conversation_id=share.conversation_id,
                shared_with_user_id=share.shared_with_user_id,
                can_edit=share.can_edit,
                can_view=share.can_view,
                shared_at=share.shared_at,
                shared_by_user_id=share.shared_by_user_id
            ) for share in shares
        ]
