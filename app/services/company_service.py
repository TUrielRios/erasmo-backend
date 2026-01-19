"""
Servicio para gestion de companias mejorado
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.models.company import Company, CompanyDocument
from app.models.user import User
from app.models.project import Project
from app.models.schemas import CompanyCreate, CompanyResponse, DocumentCategory
import os
import json

class CompanyService:
    """Servicio para operaciones con companias"""
    
    @staticmethod
    def create_company(db: Session, company_data: CompanyCreate) -> Company:
        """Crear una nueva compania"""
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
        """Obtener compania por ID"""
        return db.query(Company).filter(Company.id == company_id).first()
    
    @staticmethod
    def get_company_by_name(db: Session, name: str) -> Optional[Company]:
        """Obtener compania por nombre"""
        return db.query(Company).filter(Company.name == name).first()
    
    @staticmethod
    def get_all_companies(db: Session, skip: int = 0, limit: int = 100) -> List[Company]:
        """Obtener todas las companias con conteo de usuarios"""
        return db.query(Company).filter(Company.is_active == True).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_companies_with_user_count(db: Session) -> List[dict]:
        """Obtener companias con conteo de usuarios"""
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
        """Buscar compania existente o crear nueva"""
        # Buscar compania existente
        existing_company = CompanyService.get_company_by_name(db, name)
        if existing_company:
            return existing_company
        
        # Crear nueva compania
        company_data = CompanyCreate(
            name=name,
            industry=industry,
            sector=sector,
            description=f"Compania en {industry} - {sector}"
        )
        return CompanyService.create_company(db, company_data)
    
    @staticmethod
    def update_company(db: Session, company_id: int, company_data: dict) -> Optional[Company]:
        """Actualizar informacion de compania"""
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
        """Desactivar compania"""
        company = CompanyService.get_company_by_id(db, company_id)
        if not company:
            return False
        
        company.is_active = False
        db.commit()
        return True

    @staticmethod
    def delete_company_complete(db: Session, company_id: int) -> bool:
        """Borrado total de compania, documentos, proyectos y archivos fisicos"""
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return False
            
        try:
            # 1. Eliminar archivos fisicos de la compania
            company_docs_dir = f"documents/company_{company_id}"
            if os.path.exists(company_docs_dir):
                import shutil
                shutil.rmtree(company_docs_dir)
                print(f"[CLEANUP] Deleted company directory: {company_docs_dir}")
            
            # 2. Eliminar archivos fisicos de todos los proyectos de la compania
            projects = db.query(Project).filter(Project.company_id == company_id).all()
            for project in projects:
                project_dir = f"documents/projects/project_{project.id}"
                if os.path.exists(project_dir):
                    import shutil
                    shutil.rmtree(project_dir)
                    print(f"[CLEANUP] Deleted project directory: {project_dir}")

            # 3. Borrar de la base de datos
            # Nota: Debido a cascade="all, delete-orphan" en el modelo Company,
            # borrar la compania deberia borrar automaticamente:
            # - documents (CompanyDocument)
            # - ai_configurations (AIConfiguration)
            # - projects (Project) -> y estos a su vez sus chats, mensajes y archivos
            
            # Sin embargo, los usuarios asociados a la compania tienen company_id nullable.
            # Los dejamos como estan (huerfanos de empresa) o podriamos borrarlos si fuera necesario.
            # Por ahora los dejamos para no perder acceso administrativo si el admin pertenece a la empresa.
            
            db.delete(company)
            db.commit()
            return True
        except Exception as e:
            print(f"[ERR] Error eliminando compania {company_id}: {e}")
            db.rollback()
            return False

class CompanyDocumentService:
    """Servicio mejorado para gestion de documentos por compania"""
    
    @staticmethod
    def create_document(
        db: Session, 
        company_id: int, 
        filename: str, 
        file_path: Optional[str],
        category: DocumentCategory = DocumentCategory.KNOWLEDGE_BASE,
        description: Optional[str] = None,
        priority: int = 1
    ) -> CompanyDocument:
        """Crear registro de documento categorizado para una compania"""
        # Calculate file size only if file_path is provided
        file_size = 0
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
        
        db_document = CompanyDocument(
            company_id=company_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
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
        """Obtener documentos de una compania, opcionalmente filtrados por categoria"""
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
        """Eliminar documento de una compania"""
        document = db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id,
            CompanyDocument.company_id == company_id
        ).first()
        
        if not document:
            return False
        
        # Eliminar archivo fisico solo si existe un path
        if document.file_path and os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Marcar como inactivo en base de datos
        document.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def get_document_content(db: Session, company_id: int, document_id: int) -> Optional[str]:
        """Obtener contenido de un documento especifico"""
        document = db.query(CompanyDocument).filter(
            CompanyDocument.id == document_id,
            CompanyDocument.company_id == company_id,
            CompanyDocument.is_active == True
        ).first()
        
        if not document:
            return None
        
        # Si no tiene file_path, es un protocolo vinculado
        if not document.file_path:
            return None
            
        if not os.path.exists(document.file_path):
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
        """Obtener documentos por prioridad (1=mas alta, 5=mas baja)"""
        return db.query(CompanyDocument).filter(
            CompanyDocument.company_id == company_id,
            CompanyDocument.category == category,
            CompanyDocument.priority <= max_priority,
            CompanyDocument.is_active == True,
            CompanyDocument.processing_status.in_(["completed", "pending"])
        ).order_by(CompanyDocument.priority.asc()).all()
    
    @staticmethod
    def get_all_company_content(db: Session, company_id: int) -> dict:
        """Obtener todo el contenido de documentos de una compania organizado por categoria"""
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
            
            # Por categoria
            category = doc.category.value
            summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
            
            # Contadores especiales
            if status == "pending":
                summary["pending_processing"] += 1
            elif status == "failed":
                summary["failed_processing"] += 1
        
        return summary
