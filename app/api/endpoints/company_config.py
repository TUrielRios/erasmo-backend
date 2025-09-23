"""
Endpoints para configuración avanzada de compañías
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.db.database import get_db
from app.services.company_configuration_service import CompanyConfigurationService
from app.services.document_processing_service import DocumentProcessingService
from app.models.schemas import DocumentCategory

router = APIRouter(prefix="/company-config", tags=["company_configuration"])

@router.get("/companies/{company_id}/full-configuration")
async def get_full_company_configuration(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Obtener configuración completa de una compañía"""
    config = CompanyConfigurationService.get_full_configuration(db, company_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración de compañía no encontrada"
        )
    return config

@router.post("/companies/{company_id}/initialize-ai")
async def initialize_company_ai(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Inicializar configuración de IA para una compañía"""
    result = await CompanyConfigurationService.initialize_ai_configuration(db, company_id)
    return result

@router.post("/companies/{company_id}/process-documents")
async def process_company_documents(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Procesar todos los documentos pendientes de una compañía"""
    result = await DocumentProcessingService.process_company_documents(db, company_id)
    return result

@router.get("/companies/{company_id}/knowledge-summary")
async def get_knowledge_summary(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Obtener resumen del conocimiento procesado de una compañía"""
    summary = DocumentProcessingService.get_company_knowledge_summary(db, company_id)
    return summary

@router.get("/companies/{company_id}/ai-effectiveness")
async def get_ai_effectiveness_metrics(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Obtener métricas de efectividad de la IA"""
    metrics = CompanyConfigurationService.get_ai_effectiveness_metrics(db, company_id)
    return metrics

@router.post("/companies/{company_id}/optimize-configuration")
async def optimize_ai_configuration(
    company_id: int,
    optimization_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Optimizar configuración de IA basada en métricas de uso"""
    result = await CompanyConfigurationService.optimize_configuration(
        db, company_id, optimization_data
    )
    return result

@router.get("/companies/{company_id}/document-categories")
async def get_document_categories_status(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Obtener estado de documentos por categoría"""
    status = CompanyConfigurationService.get_document_categories_status(db, company_id)
    return status

@router.post("/companies/{company_id}/validate-setup")
async def validate_company_setup(
    company_id: int,
    db: Session = Depends(get_db)
):
    """Validar que la configuración de la compañía esté completa"""
    validation = CompanyConfigurationService.validate_company_setup(db, company_id)
    return validation

@router.get("/my-company/configuration")
async def get_my_company_configuration(
    company_id: int,  # Now requires company_id as parameter instead of getting from user
    db: Session = Depends(get_db)
):
    """Obtener configuración de la compañía (requiere company_id)"""
    config = CompanyConfigurationService.get_client_view_configuration(db, company_id)
    return config

@router.get("/my-company/ai-status")
async def get_my_company_ai_status(
    company_id: int,  # Now requires company_id as parameter instead of getting from user
    db: Session = Depends(get_db)
):
    """Obtener estado de la IA de la compañía (requiere company_id)"""
    status = CompanyConfigurationService.get_ai_status_for_client(db, company_id)
    return status
