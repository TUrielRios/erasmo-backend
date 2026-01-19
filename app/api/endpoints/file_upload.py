"""
Endpoints para cargar archivos (imagenes, documentos) al chat
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from sqlalchemy.orm import Session
import logging
from typing import List

from app.db.database import get_db
from app.services.file_processor_service import FileProcessorService
from app.services.auth_service import AuthService
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])
file_processor = FileProcessorService()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user_id: int = None,
    session_id: str = None,
    db: Session = Depends(get_db)
):
    """
    Cargar un archivo (imagen o documento) para analizar en el chat
    
    Soporta:
    - Imagenes: PNG, JPG, JPEG, GIF, WEBP
    - Documentos: PDF, DOCX, XLSX, TXT
    """
    try:
        # Validar usuario
        if user_id:
            current_user = AuthService.get_user_by_id(db, user_id)
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario no encontrado"
                )
        
        # Leer contenido del archivo
        content = await file.read()
        
        logger.info(f"[v0] Archivo subido: {file.filename} ({len(content)} bytes)")
        
        # Procesar archivo
        result = file_processor.process_file(content, file.filename)
        
        logger.info(f"[v0] Archivo procesado exitosamente: {file.filename}")
        
        return {
            "success": True,
            "filename": file.filename,
            "file_type": result.get("type"),
            "file_format": result.get("file_format"),
            "analysis": result.get("analysis"),
            "content": result.get("content", ""),
            "summary": result.get("summary"),
            "full_length": result.get("full_length"),
            "tokens_used": result.get("tokens_used", 0),
            "message": f"Archivo '{file.filename}' procesado exitosamente"
        }
        
    except ValueError as e:
        logger.error(f"Error validando archivo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error procesando archivo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando archivo: {str(e)}"
        )

@router.post("/analyze-with-message")
async def analyze_file_and_send_message(
    file: UploadFile = File(...),
    user_id: int = None,
    session_id: str = None,
    message: str = None,
    db: Session = Depends(get_db)
):
    """
    Cargar archivo y enviar mensaje con contexto del archivo al chat
    Combina el analisis del archivo con la consulta del usuario
    """
    try:
        # Procesar archivo
        file_result = file_processor.process_file(
            await file.read(),
            file.filename
        )
        
        # Preparar contexto adicional con la informacion del archivo
        file_context = ""
        if file_result.get("type") == "image":
            file_context = f"\n\n **Analisis de imagen ({file.filename}):**\n{file_result.get('analysis', '')}"
        elif file_result.get("type") == "document":
            content = file_result.get("content", "")
            summary = file_result.get("summary", "")
            file_context = f"\n\n[DOC] **Documento ({file.filename}):**\n"
            if summary:
                file_context += f"**Resumen:** {summary}\n"
            file_context += f"**Contenido:** {content}"
        
        # Retornar analisis del archivo + instruccion para enviar con mensaje
        return {
            "success": True,
            "filename": file.filename,
            "file_type": file_result.get("type"),
            "file_context": file_context,
            "message": f"Archivo '{file.filename}' analizado. Ahora puedes enviarlo junto con tu mensaje al chat.",
            "next_step": "Usar el contenido de 'file_context' al enviar el mensaje de chat"
        }
        
    except Exception as e:
        logger.error(f"Error analizando archivo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analizando archivo: {str(e)}"
        )

@router.get("/supported-formats")
async def get_supported_formats():
    """Obtener lista de formatos de archivo soportados"""
    return {
        "images": [".png", ".jpg", ".jpeg", ".gif", ".webp"],
        "documents": [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt"],
        "max_file_size_mb": 20,
        "capabilities": {
            "images": "Analisis visual con Vision API",
            "pdf": "Extraccion de texto con OCR",
            "docx": "Extraccion de texto y tablas",
            "xlsx": "Extraccion de datos de hojas",
            "txt": "Procesamiento directo"
        }
    }
