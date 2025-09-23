"""
Servicio para funcionalidades de administración
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.models.user import User
from app.models.company import Company, CompanyDocument
from app.models.conversation import Conversation, Message
from app.services.company_service import CompanyService, CompanyDocumentService

class AdminService:
    """Servicio para operaciones administrativas"""
    
    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        """Obtener estadísticas del dashboard administrativo"""
        
        # Conteos básicos
        total_companies = db.query(Company).filter(Company.is_active == True).count()
        total_users = db.query(User).filter(User.is_active == True, User.role == 'client').count()
        total_conversations = db.query(Conversation).filter(Conversation.is_active == True).count()
        total_messages = db.query(Message).count()
        
        # Actividad reciente (últimos 7 días)
        week_ago = datetime.now() - timedelta(days=7)
        new_users_week = db.query(User).filter(
            User.created_at >= week_ago,
            User.role == 'client'
        ).count()
        
        new_conversations_week = db.query(Conversation).filter(
            Conversation.created_at >= week_ago
        ).count()
        
        # Top 5 compañías por número de usuarios
        top_companies = db.query(
            Company.name,
            Company.industry,
            func.count(User.id).label('user_count')
        ).join(User).group_by(Company.id, Company.name, Company.industry)\
         .order_by(desc('user_count')).limit(5).all()
        
        # Actividad por compañía (mensajes en la última semana)
        company_activity = db.query(
            Company.name,
            func.count(Message.id).label('message_count')
        ).join(User).join(Conversation).join(Message)\
         .filter(Message.timestamp >= week_ago)\
         .group_by(Company.id, Company.name)\
         .order_by(desc('message_count')).limit(10).all()
        
        return {
            "overview": {
                "total_companies": total_companies,
                "total_users": total_users,
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "new_users_week": new_users_week,
                "new_conversations_week": new_conversations_week
            },
            "top_companies": [
                {
                    "name": name,
                    "industry": industry,
                    "user_count": user_count
                }
                for name, industry, user_count in top_companies
            ],
            "company_activity": [
                {
                    "company_name": name,
                    "message_count": message_count
                }
                for name, message_count in company_activity
            ],
            "usage_stats": {
                "popular_features": [],  # Simplified - no complex features tracking
                "document_uploads": db.query(CompanyDocument).filter(CompanyDocument.is_active == True).count()
            }
        }
    
    @staticmethod
    def get_company_details(db: Session, company_id: int) -> Optional[Dict[str, Any]]:
        """Obtener detalles completos de una compañía"""
        company = CompanyService.get_company_by_id(db, company_id)
        if not company:
            return None
        
        # Obtener usuarios de la compañía
        users = db.query(User).filter(
            User.company_id == company_id,
            User.is_active == True
        ).all()
        
        documents = CompanyDocumentService.get_company_documents(db, company_id)
        
        # Estadísticas de actividad
        total_conversations = db.query(Conversation).join(User).filter(
            User.company_id == company_id
        ).count()
        
        total_messages = db.query(Message).join(Conversation).join(User).filter(
            User.company_id == company_id
        ).count()
        
        # Actividad reciente
        week_ago = datetime.now() - timedelta(days=7)
        recent_activity = db.query(Message).join(Conversation).join(User).filter(
            User.company_id == company_id,
            Message.timestamp >= week_ago
        ).count()
        
        return {
            "company": {
                "id": company.id,
                "name": company.name,
                "industry": company.industry,
                "sector": company.sector,
                "description": company.description,
                "created_at": company.created_at,
                "is_active": company.is_active
            },
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "work_area": user.work_area,
                    "created_at": user.created_at,
                    "is_active": user.is_active
                }
                for user in users
            ],
            "documents": documents,
            "activity_stats": {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "recent_activity": recent_activity
            }
        }
    
    @staticmethod
    def get_all_companies_summary(db: Session) -> List[Dict[str, Any]]:
        """Obtener resumen de todas las compañías para el panel admin"""
        companies_data = CompanyService.get_companies_with_user_count(db)
        
        for company_data in companies_data:
            documents = CompanyDocumentService.get_company_documents(db, company_data["id"])
            company_data["document_count"] = len(documents)
            company_data["has_documents"] = len(documents) > 0
        
        return companies_data
