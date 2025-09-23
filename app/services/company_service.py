"""
Servicio para gestión de compañías mejorado
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.models.company import Company, CompanyDocument
from app.models.user import User
from app.models.schemas import CompanyCreate, CompanyResponse, DocumentCategory
import os
import json

class CompanyService:
    """Servicio para operaciones con compañías"""
    
    @staticmethod
    def create_company(db: Session, company_data: CompanyCreate) -> Company:
        """Crear una nueva compañía"""
        db_company = Company(
            name=company_data.name,
            industry=company_data.industry,
            sector=company_data.sector,
            description=company_data.description
        )
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        return db_company
    
    @staticmethod
    def get_company_by_id(db: Session, company_id: int) -> Optional[Company]:
        """Obtener compañía por ID"""
        return db.query(Company).filter(Company.id == company_id).first()
    
    @staticmethod
    def get_company_by_name(db: Session, name: str) -> Optional[Company]:
        """Obtener compañía por nombre"""
        return db.query(Company).filter(Company.name == name).first()
    
    @staticmethod
    def get_all_companies(db: Session, skip: int = 0, limit: int = 100) -> List[Company]:
        """Obtener todas las compañías con conteo de usuarios"""
        return db.query(Company).filter(Company.is_active == True).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_companies_with_user_count(db: Session) -> List[dict]:
        """Obtener compañías con conteo de usuarios"""
        result = db.query(
            Company,
            func.count(User.id).label('user_count')
        ).outerjoin(User).group_by(Company.id).filter(Company.is_active == True).all()
        
        companies = []
        for company, user_count in result:
            company_dict = {
                "id": company.id,
                "name": company.name,
                "industry": company.industry,
                "sector": company.sector,
                "description": company.description,
                "is_active": company.is_active,
                "created_at": company.created_at,
                "user_count": user_count
            }
            companies.append(company_dict)
        
        return companies
    
    @staticmethod
    def find_or_create_company(db: Session, name: str, industry: str, sector: str) -> Company:
        """Buscar compañía existente o crear nueva"""
        # Buscar compañía existente
        existing_company = CompanyService.get_company_by_name(db, name)
        if existing_company:
            return existing_company
        
        # Crear nueva compañía
        company_data = CompanyCreate(
            name=name,
            industry=industry,
            sector=sector,
            description=f"Compañía en {industry} - {sector}"
        )
        return CompanyService.create_company(db, company_data)
    
    @staticmethod
    def update_company(db: Session, company_id: int, company_data: dict) -> Optional[Company]:
        """Actualizar información de compañía"""
        company = CompanyService.get_company_by_id(db, company_id)
        if not company:
            return None
        
        for field, value in company_data.items():
            if hasattr(company, field):
                setattr(company, field, value)
        
        db.commit()
        db.refresh(company)
        return company
    
    @staticmethod
    def deactivate_company(db: Session, company_id: int) -> bool:
        """Desactivar compañía"""
        company = CompanyService.get_company_by_id(db, company_id)
        if not company:
            return False
        
        company.is_active = False
        db.commit()
        return True

class CompanyDocumentService:
    """Servicio mejorado para gestión de documentos por compañía"""
    
    @staticmethod
    def create_document(
        db: Session, 
        company_id: int, 
        filename: str, 
        file_path: str,
        category: DocumentCategory = DocumentCategory.KNOWLEDGE_BASE,
        description: Optional[str] = None,
        priority: int = 1
    ) -> CompanyDocument:
        """Crear registro de documento categorizado para una compañía"""
        db_document = CompanyDocument(
            company_id=company_id,
            filename=filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            category=category,
            description=description,
            priority=priority,
            processing_status="pending"
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        return db_document
    
    @staticmethod
    def get_company_documents(
        db: Session, 
        company_id: int, 
        category: Optional[DocumentCategory] = None
    ) -> List[CompanyDocument]:
        """Obtener documentos de una compañía, opcionalmente filtrados por categoría"""
        query = db.query(CompanyDocument).filter(
            CompanyDocument.company_id == company_id,
            CompanyDocument.is_active == True
        )
        
        if category:
            query = query.filter(CompanyDocument.category == category)
        
        return query.order_by(CompanyDocument.priority.asc(), CompanyDocument.uploaded_at.desc()).all()
    
    @staticmethod
    def get_knowledge_base_documents(db: Session, company_id: int) -> List[CompanyDocument]:
        """Obtener solo documentos de fuentes de conocimiento"""
        return CompanyDocumentService.get_company_documents(
            db, company_id, DocumentCategory.KNOWLEDGE_BASE
        )
    
    @staticmethod
    def get_instruction_documents(db: Session, company_id: int) -> List[CompanyDocument]:
        """Obtener solo documentos de instrucciones"""
        return CompanyDocumentService.get_company_documents(
            db, company_id, DocumentCategory.INSTRUCTIONS
        )
    
    @staticmethod
    def update_document(
        db: Session, 
        company_id: int, 
        document_id: int, 
        update_data: dict
    ) -> Optional[CompanyDocument]:
        """Actualizar metadatos de un documento"""
        document = db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id,
            CompanyDocument.company_id == company_id
        ).first()
        
        if not document:
            return None
        
        for field, value in update_data.items():
            if hasattr(document, field):
                setattr(document, field, value)
        
        db.commit()
        db.refresh(document)
        return document
    
    @staticmethod
    def update_processing_status(
        db: Session, 
        document_id: int, 
        status: str, 
        processed_chunks: int = 0,
        total_chunks: int = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """Actualizar estado de procesamiento de un documento"""
        document = db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id
        ).first()
        
        if not document:
            return False
        
        document.processing_status = status
        document.processed_chunks = processed_chunks
        document.total_chunks = total_chunks
        if error_message:
            document.error_message = error_message
        
        if status == "processing" and not document.processing_started_at:
            from datetime import datetime
            document.processing_started_at = datetime.utcnow()
        elif status in ["completed", "failed"]:
            from datetime import datetime
            document.processing_completed_at = datetime.utcnow()
        
        db.commit()
        return True
    
    @staticmethod
    def delete_document(db: Session, company_id: int, document_id: int) -> bool:
        """Eliminar documento de una compañía"""
        document = db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id,
            CompanyDocument.company_id == company_id
        ).first()
        
        if not document:
            return False
        
        # Eliminar archivo físico
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Marcar como inactivo en base de datos
        document.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def get_document_content(db: Session, company_id: int, document_id: int) -> Optional[str]:
        """Obtener contenido de un documento específico"""
        document = db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id,
            CompanyDocument.company_id == company_id,
            CompanyDocument.is_active == True
        ).first()
        
        if not document or not os.path.exists(document.file_path):
            return None
        
        try:
            with open(document.file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception:
            return None
    
    @staticmethod
    def get_documents_by_priority(
        db: Session, 
        company_id: int, 
        category: DocumentCategory,
        max_priority: int = 3
    ) -> List[CompanyDocument]:
        """Obtener documentos por prioridad (1=más alta, 5=más baja)"""
        return db.query(CompanyDocument).filter(
            CompanyDocument.company_id == company_id,
            CompanyDocument.category == category,
            CompanyDocument.priority <= max_priority,
            CompanyDocument.is_active == True,
            CompanyDocument.processing_status.in_(["completed", "pending"])
        ).order_by(CompanyDocument.priority.asc()).all()
    
    @staticmethod
    def get_all_company_content(db: Session, company_id: int) -> dict:
        """Obtener todo el contenido de documentos de una compañía organizado por categoría"""
        knowledge_docs = CompanyDocumentService.get_knowledge_base_documents(db, company_id)
        instruction_docs = CompanyDocumentService.get_instruction_documents(db, company_id)
        
        content = {
            "knowledge_base": [],
            "instructions": [],
            "company_info": []
        }
        
        # Procesar documentos de conocimiento
        for doc in knowledge_docs:
            if doc.processing_status in ["completed", "pending"]:
                doc_content = CompanyDocumentService.get_document_content(db, company_id, doc.id)
                if doc_content:
                    content["knowledge_base"].append({
                        "filename": doc.filename,
                        "content": doc_content,
                        "priority": doc.priority,
                        "description": doc.description
                    })
        
        # Procesar documentos de instrucciones
        for doc in instruction_docs:
            if doc.processing_status in ["completed", "pending"]:
                doc_content = CompanyDocumentService.get_document_content(db, company_id, doc.id)
                if doc_content:
                    content["instructions"].append({
                        "filename": doc.filename,
                        "content": doc_content,
                        "priority": doc.priority,
                        "description": doc.description
                    })
        
        return content
    
    @staticmethod
    def get_processing_summary(db: Session, company_id: int) -> dict:
        """Obtener resumen del estado de procesamiento de documentos"""
        documents = db.query(CompanyDocument).filter(
            CompanyDocument.company_id == company_id,
            CompanyDocument.is_active == True
        ).all()
        
        summary = {
            "total_documents": len(documents),
            "by_status": {},
            "by_category": {},
            "pending_processing": 0,
            "failed_processing": 0
        }
        
        for doc in documents:
            # Por estado
            status = doc.processing_status
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Por categoría
            category = doc.category.value
            summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
            
            # Contadores especiales
            if status == "pending":
                summary["pending_processing"] += 1
            elif status == "failed":
                summary["failed_processing"] += 1
        
        return summary
