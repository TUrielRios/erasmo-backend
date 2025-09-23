"""
Endpoints de administración mejorados para personalización de IA
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.db.database import get_db
from app.services.admin_service import AdminService
from app.services.company_service import CompanyService, CompanyDocumentService
from app.services.ai_configuration_service import AIConfigurationService
from app.services.ingestion_service import IngestionService
from app.models.schemas import (
    CompanyResponse, 
    DocumentCategory, 
    AdminCompanyDocumentUpload,
    AIConfigurationCreate,
    AIConfigurationUpdate,
    AIConfigurationResponse,
    CompanyDocumentResponse,
    IngestionType
)
from app.models.user import User
import os
import shutil
import json

router = APIRouter(prefix="/admin", tags=["administration"])

@router.get("/dashboard")
async def get_admin_dashboard(
    db: Session = Depends(get_db)
):
    """Obtener estadísticas del dashboard administrativo"""
    return AdminService.get_dashboard_stats(db)

@router.get("/companies", response_model=List[Dict[str, Any]])
async def get_all_companies(
    db: Session = Depends(get_db)
):
    """Obtener todas las compañías con resumen"""
    return AdminService.get_all_companies_summary(db)

@router.get("/companies/{company_id}")
async def get_company_details(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Obtener detalles completos de una compañía"""
    company_details = AdminService.get_company_details(db, company_id)
    if not company_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compañía no encontrada"
        )
    return company_details

@router.post("/companies/{company_id}/documents")
async def upload_company_documents(
    company_id: int,
    files: List[UploadFile] = File(...),
    category: DocumentCategory = Form(...),
    description: Optional[str] = Form(None),
    priority: int = Form(1),
    vectorize: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Cargar documentos categorizados para personalizar la IA de una compañía"""
    # Verificar que la compañía existe
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compañía no encontrada"
        )
    
    uploaded_files = []
    failed_files = []
    
    ingestion_service = IngestionService() if vectorize else None
    
    for file in files:
        # Solo permitir archivos .txt
        if not file.filename.endswith('.txt'):
            failed_files.append({
                "filename": file.filename,
                "error": "Solo se permiten archivos .txt"
            })
            continue
        
        try:
            # Crear directorio para la compañía si no existe
            company_dir = f"documents/company_{company_id}/{category.value}"
            os.makedirs(company_dir, exist_ok=True)
            
            # Leer contenido del archivo
            content = await file.read()
            
            # Guardar archivo
            file_path = f"{company_dir}/{file.filename}"
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # Registrar en base de datos con categoría
            document = CompanyDocumentService.create_document(
                db, 
                company_id, 
                file.filename, 
                file_path,
                category=category,
                description=description,
                priority=priority
            )
            
            chunk_ids = []
            if vectorize and ingestion_service:
                try:
                    # Prepare metadata for vectorization
                    vectorization_metadata = {
                        "company_id": company_id,
                        "category": category.value,
                        "description": description,
                        "priority": priority,
                        "document_id": document.id,
                        "ingestion_type": "knowledge",
                        "dimension": category.value,
                        "modelo_base": "company_specific",
                        "tipo_output": "conceptual-accional"
                    }
                    
                    # Vectorize the document
                    chunk_ids = await ingestion_service.process_knowledge_file(
                        content,
                        file.filename,
                        vectorization_metadata
                    )
                    
                    print(f"✅ Vectorized {file.filename} with {len(chunk_ids)} chunks for company {company_id}")
                    
                except Exception as e:
                    print(f"⚠️ Error vectorizing {file.filename}: {str(e)}")
                    # Continue without failing the upload
            
            uploaded_files.append({
                "id": document.id,
                "filename": file.filename,
                "category": category.value,
                "description": description,
                "priority": priority,
                "size": os.path.getsize(file_path),
                "vectorized": len(chunk_ids) > 0,
                "chunks_created": len(chunk_ids)
            })
            
        except Exception as e:
            failed_files.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "message": f"Procesados {len(uploaded_files)} archivos exitosamente",
        "uploaded_files": uploaded_files,
        "failed_files": failed_files,
        "vectorization_enabled": vectorize
    }

@router.get("/companies/{company_id}/documents")
async def get_company_documents(
    company_id: int,
    category: Optional[DocumentCategory] = None,
    db: Session = Depends(get_db)
):
    """Obtener lista de documentos de una compañía, opcionalmente filtrados por categoría"""
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compañía no encontrada"
        )
    
    documents = CompanyDocumentService.get_company_documents(db, company_id, category)
    
    # Agrupar documentos por categoría
    documents_by_category = {}
    for doc in documents:
        cat = doc.category
        if cat not in documents_by_category:
            documents_by_category[cat] = []
        documents_by_category[cat].append(doc)
    
    return {
        "company_id": company_id,
        "company_name": company.name,
        "documents_by_category": documents_by_category,
        "total_documents": len(documents)
    }

@router.put("/companies/{company_id}/documents/{document_id}")
async def update_company_document(
    company_id: int,
    document_id: int,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Actualizar metadatos de un documento"""
    document = CompanyDocumentService.update_document(db, company_id, document_id, update_data)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    return {
        "message": "Documento actualizado exitosamente",
        "document": CompanyDocumentResponse.from_orm(document)
    }

@router.delete("/companies/{company_id}/documents/{document_id}")
async def delete_company_document(
    company_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    """Eliminar un documento de una compañía"""
    success = CompanyDocumentService.delete_document(db, company_id, document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    return {"message": "Documento eliminado exitosamente"}

@router.post("/companies/{company_id}/ai-configuration", response_model=AIConfigurationResponse)
async def create_ai_configuration(
    company_id: int,
    config_data: AIConfigurationCreate,
    db: Session = Depends(get_db)
):
    """Crear configuración de IA para una compañía"""
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compañía no encontrada"
        )
    
    config_data.company_id = company_id
    ai_config = AIConfigurationService.create_configuration(db, config_data)
    
    return AIConfigurationResponse.from_orm(ai_config)

@router.get("/companies/{company_id}/ai-configuration", response_model=AIConfigurationResponse)
async def get_ai_configuration(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Obtener configuración de IA de una compañía"""
    ai_config = AIConfigurationService.get_by_company_id(db, company_id)
    if not ai_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración de IA no encontrada"
        )
    
    return AIConfigurationResponse.from_orm(ai_config)

@router.put("/companies/{company_id}/ai-configuration", response_model=AIConfigurationResponse)
async def update_ai_configuration(
    company_id: int,
    config_update: AIConfigurationUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar configuración de IA de una compañía"""
    ai_config = AIConfigurationService.update_configuration(db, company_id, config_update)
    if not ai_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración de IA no encontrada"
        )
    
    return AIConfigurationResponse.from_orm(ai_config)

@router.post("/companies/{company_id}/ai-configuration/test")
async def test_ai_configuration(
    company_id: int,
    test_message: str = Form(...),
    db: Session = Depends(get_db)
):
    """Probar la configuración de IA con un mensaje de prueba"""
    ai_config = AIConfigurationService.get_by_company_id(db, company_id)
    if not ai_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración de IA no encontrada"
        )
    
    # Aquí implementarías la lógica de prueba
    # Por ahora retornamos un placeholder
    return {
        "message": "Prueba de configuración de IA",
        "test_input": test_message,
        "ai_response": "Esta sería la respuesta de la IA configurada",
        "configuration_used": {
            "model": ai_config.model_name,
            "temperature": ai_config.temperature,
            "response_style": ai_config.response_style
        }
    }

@router.put("/companies/{company_id}/status")
async def update_company_status(
    company_id: int,
    status_data: Dict[str, bool],
    db: Session = Depends(get_db)
):
    """Activar/desactivar compañía"""
    is_active = status_data.get("is_active", True)
    
    if is_active:
        company = CompanyService.update_company(db, company_id, {"is_active": True})
    else:
        success = CompanyService.deactivate_company(db, company_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Compañía no encontrada"
            )
        company = CompanyService.get_company_by_id(db, company_id)
    
    return {
        "message": f"Compañía {'activada' if is_active else 'desactivada'} exitosamente",
        "company": CompanyResponse.from_orm(company)
    }

@router.post("/companies/{company_id}/documents/bulk-update")
async def bulk_update_documents(
    company_id: int,
    updates: List[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """Actualizar múltiples documentos en lote"""
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compañía no encontrada"
        )
    
    updated_documents = []
    failed_updates = []
    
    for update in updates:
        document_id = update.get("document_id")
        update_data = {k: v for k, v in update.items() if k != "document_id"}
        
        try:
            document = CompanyDocumentService.update_document(db, company_id, document_id, update_data)
            if document:
                updated_documents.append(document.id)
            else:
                failed_updates.append({"document_id": document_id, "error": "Documento no encontrado"})
        except Exception as e:
            failed_updates.append({"document_id": document_id, "error": str(e)})
    
    return {
        "message": f"Actualizados {len(updated_documents)} documentos",
        "updated_documents": updated_documents,
        "failed_updates": failed_updates
    }

@router.get("/companies/{company_id}/analytics")
async def get_company_analytics(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Obtener analíticas de uso de la compañía"""
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Compañía no encontrada"
        )
    
    analytics = AdminService.get_company_analytics(db, company_id)
    return analytics
