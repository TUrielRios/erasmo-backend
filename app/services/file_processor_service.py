"""
Servicio para procesar archivos (imágenes, PDFs, documentos)
Integra vision API de OpenAI y extracción de texto
"""

import os
import base64
from typing import Optional, Dict, Any
from pathlib import Path
import logging
from openai import OpenAI
from app.utils.file_extractor import FileExtractor

logger = logging.getLogger(__name__)

class FileProcessorService:
    """Servicio para procesar archivos: imágenes, PDFs, documentos"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.supported_image_types = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
        self.supported_document_types = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".pptx", ".ppt", ".md"}
        self.max_file_size = 20 * 1024 * 1024  # 20MB
    
    def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Procesa cualquier archivo soportado y extrae información
        
        Args:
            file_content: Contenido del archivo en bytes
            filename: Nombre del archivo
            
        Returns:
            Dict con tipo, contenido extraído y metadatos
        """
        file_ext = Path(filename).suffix.lower()
        
        # Validar tamaño
        if len(file_content) > self.max_file_size:
            raise ValueError(f"Archivo demasiado grande. Máximo {self.max_file_size / 1024 / 1024}MB")
        
        logger.info(f"[v0] Procesando archivo: {filename} ({len(file_content)} bytes)")
        
        if file_ext in self.supported_image_types:
            return self._process_image(file_content, filename)
        elif file_ext in self.supported_document_types:
            return self._process_document(file_content, filename)
        else:
            raise ValueError(f"Tipo de archivo no soportado: {file_ext}")
    
    def _process_image(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Procesa imágenes con Vision API de OpenAI"""
        logger.info(f"[v0] Procesando imagen: {filename}")
        
        # Convertir a base64
        base64_image = base64.standard_b64encode(file_content).decode("utf-8")
        
        try:
            # Llamar a Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            },
                            {
                                "type": "text",
                                "text": """Analiza esta imagen en detalle. Proporciona:
1. Descripción general de la imagen
2. Elementos principales identificados
3. Texto visible en la imagen (si existe)
4. Contexto o propósito probable
5. Datos o números importantes (si aplica)

Sé muy específico y detallado en tu análisis."""
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            
            analysis = response.choices[0].message.content
            
            logger.info(f"[v0] Análisis de imagen completado: {len(analysis)} caracteres")
            
            return {
                "type": "image",
                "filename": filename,
                "analysis": analysis,
                "file_size": len(file_content),
                "tokens_used": response.usage.completion_tokens
            }
            
        except Exception as e:
            logger.error(f"Error procesando imagen: {str(e)}")
            raise
    
    def _process_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Procesa documentos (PDF, DOCX, XLSX, TXT)"""
        file_ext = Path(filename).suffix.lower()
        
        logger.info(f"[v0] Procesando documento: {filename} ({file_ext})")
        
        try:
            # Usar FileExtractor para extraer texto de cualquier formato soportado
            text = FileExtractor.extract_text(file_content, filename)
            
            if not text:
                logger.warning(f"[v0] No se pudo extraer texto de {filename}")
                text = "[No se pudo extraer texto del documento]"
            
            # Limpiar y resumir el texto si es muy largo
            text = text.strip()
            if len(text) > 10000:
                # Para documentos muy largos, usar resumen con API
                summary = self._summarize_text(text)
                logger.info(f"[v0] Documento resumido: {len(text)} -> {len(summary)} caracteres")
                return {
                    "type": "document",
                    "filename": filename,
                    "file_format": file_ext,
                    "content": text[:5000],  # Primeros 5000 caracteres
                    "summary": summary,
                    "full_length": len(text),
                    "file_size": len(file_content)
                }
            
            logger.info(f"[v0] Documento procesado: {len(text)} caracteres")
            
            return {
                "type": "document",
                "filename": filename,
                "file_format": file_ext,
                "content": text,
                "file_size": len(file_content)
            }
            
        except Exception as e:
            logger.error(f"Error procesando documento: {str(e)}")
            raise
    
    def _summarize_text(self, text: str) -> str:
        """Resumir texto largo usando API de OpenAI"""
        logger.info(f"[v0] Resumiendo texto largo ({len(text)} caracteres)...")
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"""Resume el siguiente texto en máximo 1500 palabras, 
capturando los puntos clave, números importantes y conclusiones principales:

{text}"""
                    }
                ],
                max_tokens=2000
            )
            
            summary = response.choices[0].message.content
            logger.info(f"[v0] Resumen completado: {len(summary)} caracteres")
            return summary
            
        except Exception as e:
            logger.error(f"Error resumiendo texto: {str(e)}")
            return text[:1500]  # Fallback
