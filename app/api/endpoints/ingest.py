"""
Endpoints para ingesta de conocimiento
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from typing import List, Optional
import aiofiles
import os
from datetime import datetime

from app.models.schemas import IngestRequest, IngestResponse, DocumentMetadata, DocumentType, IngestionType
from app.services.ingestion_service import IngestionService
from app.core.config import settings

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    files: List[UploadFile] = File(...),
    ingestion_type: IngestionType = IngestionType.KNOWLEDGE,
    dimension: str = "general",
    modelo_base: str = "estratégico",
    tipo_output: str = "conceptual-accional",
    company_id: Optional[int] = Form(None)
):
    """
    Ingesta de documentos .txt y .md para indexación semántica o configuración de personalidad
    
    Args:
        files: Lista de archivos a procesar
        ingestion_type: Tipo de ingesta (personality o knowledge)
        dimension: Dimensión del conocimiento (estrategia, liderazgo, etc.)
        modelo_base: Modelo conceptual base
        tipo_output: Tipo de salida esperada
        company_id: ID de la empresa (opcional, para filtrado por empresa)
    
    Returns:
        IngestResponse con resultados del procesamiento
    """
    
    processed_files = []
    failed_files = []
    total_chunks = 0
    metadata_list = []
    
    ingestion_service = IngestionService()
    
    for file in files:
        try:
            # Validar tipo de archivo
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in settings.ALLOWED_FILE_TYPES:
                failed_files.append(f"{file.filename}: Tipo de archivo no soportado")
                continue
            
            # Validar tamaño de archivo
            content = await file.read()
            if len(content) > settings.MAX_FILE_SIZE:
                failed_files.append(f"{file.filename}: Archivo demasiado grande")
                continue
            
            print(f"🔄 Procesando archivo: {file.filename} como {ingestion_type.value}")
            
            additional_metadata = {
                "ingestion_type": ingestion_type.value,
                "dimension": dimension,
                "modelo_base": modelo_base,
                "tipo_output": tipo_output,
                "file_size": len(content)
            }
            
            # Include company_id in metadata if provided
            if company_id is not None:
                additional_metadata["company_id"] = company_id
                print(f"📋 Including company_id {company_id} for file {file.filename}")
            
            if ingestion_type == IngestionType.PERSONALITY:
                chunk_ids = await ingestion_service.process_personality_file(
                    content, 
                    file.filename, 
                    additional_metadata
                )
            else:
                chunk_ids = await ingestion_service.process_knowledge_file(
                    content, 
                    file.filename, 
                    additional_metadata
                )
            
            chunks_count = len(chunk_ids)
            total_chunks += chunks_count
            
            # Crear metadatos para respuesta
            doc_metadata = DocumentMetadata(
                filename=file.filename,
                file_type=DocumentType.TXT if file_extension == ".txt" else DocumentType.MARKDOWN,
                ingestion_type=ingestion_type,
                dimension=dimension,
                modelo_base=modelo_base,
                tipo_output=tipo_output,
                file_size=len(content),
                chunk_count=chunks_count
            )
            
            metadata_list.append(doc_metadata)
            processed_files.append(file.filename)
            
            print(f"✅ Archivo {file.filename} procesado: {chunks_count} chunks")
            
        except Exception as e:
            print(f"❌ Error procesando {file.filename}: {str(e)}")
            failed_files.append(f"{file.filename}: Error - {str(e)}")
    
    return IngestResponse(
        success=len(processed_files) > 0,
        message=f"Procesados {len(processed_files)} archivos, {len(failed_files)} fallaron",
        processed_files=processed_files,
        failed_files=failed_files,
        total_chunks=total_chunks,
        metadata=[doc_metadata.model_dump() for doc_metadata in metadata_list]
    )

@router.post("/ingest/personality", response_model=IngestResponse)
async def ingest_personality_documents(
    files: List[UploadFile] = File(...),
    replace_existing: bool = False
):
    """
    Endpoint específico para configurar la personalidad del agente
    
    Args:
        files: Archivos que definen el comportamiento, tono y estilo del agente
        replace_existing: Si True, reemplaza la personalidad existente
    
    Returns:
        IngestResponse con resultados del procesamiento
    """
    
    ingestion_service = IngestionService()
    
    # Clear existing personality if requested
    if replace_existing:
        await ingestion_service.clear_personality()
        print("🧹 Personalidad existente eliminada")
    
    # Process files as personality configuration
    return await ingest_documents(
        files=files,
        ingestion_type=IngestionType.PERSONALITY,
        dimension="personalidad",
        modelo_base="protocolo_conversacional",
        tipo_output="estilo_comunicacion"
    )

@router.get("/ingest/personality")
async def get_personality_config():
    """
    Obtiene la configuración actual de personalidad del agente
    """
    
    try:
        ingestion_service = IngestionService()
        personality_config = ingestion_service.get_personality_config()
        
        return {
            "status": "success",
            "personality": personality_config,
            "timestamp": datetime.now()
        }
    except Exception as e:
        print(f"❌ Error obteniendo configuración de personalidad: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "personality": {
                "status": "no_personality_configured",
                "message": "Error al obtener configuración",
                "files": []
            },
            "timestamp": datetime.now()
        }

@router.delete("/ingest/personality")
async def clear_personality_config():
    """
    Elimina la configuración de personalidad actual
    """
    
    try:
        ingestion_service = IngestionService()
        success = await ingestion_service.clear_personality()
        
        return {
            "success": success,
            "message": "Configuración de personalidad eliminada" if success else "Error eliminando personalidad",
            "timestamp": datetime.now()
        }
    except Exception as e:
        print(f"❌ Error eliminando personalidad: {str(e)}")
        return {
            "success": False,
            "message": f"Error eliminando personalidad: {str(e)}",
            "timestamp": datetime.now()
        }

@router.get("/ingest/status")
async def get_ingestion_status():
    """
    Obtiene el estado actual del sistema de ingesta
    """
    
    try:
        ingestion_service = IngestionService()
        stats = await ingestion_service.get_document_stats()
        
        return {
            "status": "ready",
            "total_documents": stats["total_documents"],
            "total_chunks": stats["total_chunks"],
            "last_ingestion": stats["last_update"],
            "supported_formats": settings.ALLOWED_FILE_TYPES,
            "max_file_size": settings.MAX_FILE_SIZE,
            "storage_info": {
                "total_embeddings": stats["total_embeddings"],
                "storage_size": stats["storage_size"]
            }
        }
    except Exception as e:
        print(f"❌ Error obteniendo stats: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "total_documents": 0,
            "total_chunks": 0,
            "last_ingestion": None,
            "supported_formats": settings.ALLOWED_FILE_TYPES,
            "max_file_size": settings.MAX_FILE_SIZE
        }

@router.delete("/ingest/clear")
async def clear_knowledge_base():
    """
    Limpia toda la base de conocimiento (usar con precaución)
    """
    
    # Implementar limpieza real de vector DB
    try:
        ingestion_service = IngestionService()
        await ingestion_service.clear_knowledge_base()
        
        return {
            "message": "Base de conocimiento limpiada",
            "timestamp": datetime.now(),
            "documents_removed": ingestion_service.documents_removed,
            "chunks_removed": ingestion_service.chunks_removed
        }
    except Exception as e:
        print(f"❌ Error limpiando base de conocimiento: {str(e)}")
        return {
            "message": "Error al limpiar base de conocimiento",
            "timestamp": datetime.now(),
            "error": str(e)
        }

@router.post("/ingest/company/{company_id}", response_model=IngestResponse)
async def ingest_company_documents(
    company_id: int,
    files: List[UploadFile] = File(...),
    ingestion_type: IngestionType = IngestionType.KNOWLEDGE,
    dimension: str = "general",
    modelo_base: str = "estratégico",
    tipo_output: str = "conceptual-accional"
):
    """
    Endpoint específico para ingesta de documentos de una empresa específica
    
    Este endpoint permite subir documentos que serán asociados únicamente a la empresa especificada,
    garantizando el aislamiento de datos entre diferentes empresas.
    
    Args:
        company_id: ID de la empresa (requerido para filtrado por empresa)
        files: Lista de archivos a procesar (.txt, .md)
        ingestion_type: Tipo de ingesta (personality o knowledge)
        dimension: Dimensión del conocimiento (estrategia, liderazgo, etc.)
        modelo_base: Modelo conceptual base
        tipo_output: Tipo de salida esperada
    
    Returns:
        IngestResponse con resultados del procesamiento
        
    Example:
        POST /api/v1/ingest/company/123
        - Todos los documentos se asociarán a la empresa con ID 123
        - Solo usuarios de esa empresa podrán acceder a estos documentos
    """
    
    print(f"🏢 Iniciando ingesta para empresa ID: {company_id}")
    
    return await ingest_documents(
        files=files,
        ingestion_type=ingestion_type,
        dimension=dimension,
        modelo_base=modelo_base,
        tipo_output=tipo_output,
        company_id=company_id
    )
