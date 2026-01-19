"""
Endpoints para transcripcion de audio usando Whisper de OpenAI
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import openai
from app.core.config import settings
import tempfile
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...)
):
    """
    Transcribe un archivo de audio a texto usando Whisper de OpenAI
    
    Args:
        audio: Archivo de audio (mp3, wav, m4a, webm, etc.)
    
    Returns:
        JSONResponse con el texto transcrito
    """
    
    temp_audio_path = None
    
    try:
        logger.info(f"[v0] Iniciando transcripcion: {audio.filename}, tipo: {audio.content_type}")
        
        # Validar que sea un archivo de audio
        allowed_audio_types = [
            "audio/mpeg", "audio/mp3", "audio/wav", "audio/m4a",
            "audio/webm", "audio/ogg", "audio/flac"
        ]
        
        if audio.content_type not in allowed_audio_types:
            logger.warning(f"[v0] Tipo de archivo no permitido: {audio.content_type}")
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no soportado. Tipos permitidos: {', '.join(allowed_audio_types)}"
            )
        
        # Leer el contenido del archivo
        audio_content = await audio.read()
        logger.info(f"[v0] Audio leido: {len(audio_content)} bytes")
        
        # Validar tamano (25MB maximo para Whisper)
        max_size = 25 * 1024 * 1024  # 25MB
        if len(audio_content) > max_size:
            logger.error(f"[v0] Archivo demasiado grande: {len(audio_content)} bytes")
            raise HTTPException(
                status_code=400,
                detail="El archivo de audio es demasiado grande. Maximo 25MB."
            )
        
        # Crear un archivo temporal para el audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio.write(audio_content)
            temp_audio_path = temp_audio.name
        
        logger.info(f"[v0] Archivo temporal creado: {temp_audio_path}")
        
        try:
            # Inicializar cliente de OpenAI
            logger.info("[v0] Inicializando cliente OpenAI...")
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Transcribir usando Whisper con timeout
            logger.info("[v0] Enviando a Whisper para transcripcion (timeout 60s)...")
            with open(temp_audio_path, "rb") as audio_file:
                transcript = await asyncio.wait_for(
                    asyncio.to_thread(
                        client.audio.transcriptions.create,
                        model="whisper-1",
                        file=audio_file,
                        language="es"  # Forzar espanol
                    ),
                    timeout=60.0
                )
            
            logger.info(f"[OK] Audio transcrito exitosamente: {audio.filename}")
            logger.info(f"[v0] Texto transcrito: {transcript.text}")
            
            return JSONResponse(content={
                "success": True,
                "text": transcript.text,
                "filename": audio.filename
            })
        
        except asyncio.TimeoutError:
            logger.error("[v0] Timeout esperando respuesta de Whisper (60s)")
            raise HTTPException(
                status_code=504,
                detail="Timeout procesando audio con Whisper. Intenta con un archivo mas corto."
            )
            
        finally:
            # Limpiar archivo temporal
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
                logger.info(f"[v0] Archivo temporal eliminado: {temp_audio_path}")
    
    except openai.OpenAIError as e:
        logger.error(f"[ERR] Error de OpenAI transcribiendo audio: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error transcribiendo audio: {str(e)}"
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"[ERR] Error inesperado transcribiendo audio: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando audio: {str(e)}"
        )
