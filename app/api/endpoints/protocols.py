"""
Endpoints para gestion de protocolos centralizados
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging

from app.db.database import get_db
from app.models.protocol import Protocol
from app.models.company import CompanyDocument
from app.models.schemas import ProtocolCreate, ProtocolUpdate, ProtocolResponse
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/protocols", tags=["protocols"])

@router.post("/", response_model=ProtocolResponse, status_code=status.HTTP_201_CREATED)
async def create_protocol(
    protocol: ProtocolCreate,
    db: Session = Depends(get_db)
):
    """Crear nuevo protocolo centralizado"""
    logger.info(f"[PROTOCOL] Creating new protocol: {protocol.name}")
    
    # Verificar que el nombre no exista
    existing = db.query(Protocol).filter(Protocol.name == protocol.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un protocolo con el nombre '{protocol.name}'"
        )
    
    new_protocol = Protocol(
        **protocol.dict(),
        created_by_user_id=None  # TODO: Add auth
    )
    
    db.add(new_protocol)
    db.commit()
    db.refresh(new_protocol)
    
    # Agregar usage_count
    new_protocol.usage_count = 0
    
    logger.info(f"[PROTOCOL] Protocol created: ID {new_protocol.id}")
    return new_protocol

@router.get("/", response_model=List[ProtocolResponse])
async def list_protocols(
    category: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Listar todos los protocolos con conteo de uso"""
    logger.info(f"[PROTOCOL] Listing protocols (category={category}, active_only={active_only})")
    
    query = db.query(Protocol)
    
    if active_only:
        query = query.filter(Protocol.is_active == True)
    if category:
        query = query.filter(Protocol.category == category)
    
    protocols = query.order_by(Protocol.created_at.desc()).all()
    
    # Agregar usage_count a cada protocolo
    for protocol in protocols:
        usage_count = db.query(CompanyDocument).filter(
            CompanyDocument.protocol_id == protocol.id,
            CompanyDocument.use_protocol == True
        ).count()
        protocol.usage_count = usage_count
    
    logger.info(f"[PROTOCOL] Found {len(protocols)} protocols")
    return protocols

@router.get("/{protocol_id}", response_model=ProtocolResponse)
async def get_protocol(
    protocol_id: int,
    db: Session = Depends(get_db)
):
    """Obtener protocolo por ID con conteo de uso"""
    logger.info(f"[PROTOCOL] Getting protocol ID: {protocol_id}")
    
    protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protocolo no encontrado"
        )
    
    # Contar documentos que usan este protocolo
    usage_count = db.query(CompanyDocument).filter(
        CompanyDocument.protocol_id == protocol_id,
        CompanyDocument.use_protocol == True
    ).count()
    protocol.usage_count = usage_count
    
    return protocol

@router.put("/{protocol_id}", response_model=ProtocolResponse)
async def update_protocol(
    protocol_id: int,
    protocol_update: ProtocolUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualizar protocolo (afecta automaticamente a TODOS los documentos que lo referencian)
    """
    logger.info(f"[PROTOCOL] Updating protocol ID: {protocol_id}")
    
    protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protocolo no encontrado"
        )
    
    # Verificar nombre unico si se esta cambiando
    if protocol_update.name and protocol_update.name != protocol.name:
        existing = db.query(Protocol).filter(
            Protocol.name == protocol_update.name,
            Protocol.id != protocol_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un protocolo con el nombre '{protocol_update.name}'"
            )
    
    # Actualizar campos
    for key, value in protocol_update.dict(exclude_unset=True).items():
        setattr(protocol, key, value)
    
    db.commit()
    db.refresh(protocol)
    
    # Contar uso
    usage_count = db.query(CompanyDocument).filter(
        CompanyDocument.protocol_id == protocol_id,
        CompanyDocument.use_protocol == True
    ).count()
    protocol.usage_count = usage_count
    
    logger.info(f"[PROTOCOL] Protocol updated: ID {protocol_id}, affects {usage_count} documents")
    return protocol

@router.delete("/{protocol_id}")
async def delete_protocol(
    protocol_id: int,
    force: bool = False,
    db: Session = Depends(get_db)
):
    """
    Eliminar protocolo
    Si force=False, solo permite eliminar si no esta siendo usado
    Si force=True, desreferencia documentos y elimina
    """
    logger.info(f"[PROTOCOL] Deleting protocol ID: {protocol_id} (force={force})")
    
    protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protocolo no encontrado"
        )
    
    # Contar documentos que lo usan
    usage_count = db.query(CompanyDocument).filter(
        CompanyDocument.protocol_id == protocol_id,
        CompanyDocument.use_protocol == True
    ).count()
    
    if usage_count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar: {usage_count} documentos estan usando este protocolo. Use force=true para forzar la eliminacion."
        )
    
    # Desreferenciar documentos
    if usage_count > 0:
        db.query(CompanyDocument).filter(
            CompanyDocument.protocol_id == protocol_id
        ).update({"protocol_id": None, "use_protocol": False})
        logger.info(f"[PROTOCOL] Dereferenced {usage_count} documents")
    
    db.delete(protocol)
    db.commit()
    
    logger.info(f"[PROTOCOL] Protocol deleted: ID {protocol_id}")
    return {
        "success": True,
        "message": "Protocolo eliminado exitosamente",
        "dereferenced_documents": usage_count
    }

@router.get("/{protocol_id}/usage")
async def get_protocol_usage(
    protocol_id: int,
    db: Session = Depends(get_db)
):
    """Ver que documentos/sub-agentes estan usando este protocolo"""
    logger.info(f"[PROTOCOL] Getting usage for protocol ID: {protocol_id}")
    
    protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Protocolo no encontrado"
        )
    
    docs = db.query(CompanyDocument).filter(
        CompanyDocument.protocol_id == protocol_id,
        CompanyDocument.use_protocol == True
    ).all()
    
    # Agrupar por compania
    usage_by_company = {}
    for doc in docs:
        company_id = doc.company_id
        if company_id not in usage_by_company:
            usage_by_company[company_id] = {
                "company_id": company_id,
                "company_name": doc.company.name if doc.company else "Unknown",
                "documents": []
            }
        
        usage_by_company[company_id]["documents"].append({
            "id": doc.id,
            "filename": doc.filename,
            "category": doc.category.value if doc.category else None,
            "priority": doc.priority,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
        })
    
    return {
        "protocol_id": protocol_id,
        "protocol_name": protocol.name,
        "protocol_version": protocol.version,
        "total_usage_count": len(docs),
        "usage_by_company": list(usage_by_company.values())
    }

@router.get("/categories/list")
async def list_categories(
    db: Session = Depends(get_db)
):
    """Listar todas las categorias unicas de protocolos"""
    categories = db.query(Protocol.category).distinct().filter(
        Protocol.category.isnot(None),
        Protocol.is_active == True
    ).all()
    
    return {
        "categories": [cat[0] for cat in categories if cat[0]]
    }
