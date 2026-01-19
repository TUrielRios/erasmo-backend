"""
Servicio para manejar archivos adjuntos en conversaciones
Integra analisis de archivos con el contexto del chat
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class AttachmentHandlerService:
    """Gestiona archivos adjuntos en mensajes de chat"""
    
    @staticmethod
    def format_attachments_for_context(attachments: Optional[List[Dict[str, Any]]]) -> str:
        """
        Formatea los archivos adjuntos para incluir en el contexto del prompt
        
        Args:
            attachments: Lista de archivos procesados
            
        Returns:
            String formateado con el contexto de los archivos
        """
        if not attachments:
            return ""
        
        context = "\n\n[ATTACH] CONTEXTO DE ARCHIVOS ADJUNTOS:\n"
        context += "=" * 60 + "\n"
        
        for i, attachment in enumerate(attachments, 1):
            file_type = attachment.get("type") or attachment.get("file_type", "unknown")
            filename = attachment.get("filename", "Sin nombre")
            
            if file_type == "image":
                context += f"\n[{i}]  Imagen: {filename}\n"
                context += f"Analisis:\n{attachment.get('analysis', 'Sin analisis')}\n"
            
            elif file_type == "document":
                context += f"\n[{i}] [DOC] Documento: {filename}\n"
                file_format = attachment.get("file_format", "")
                
                if attachment.get("summary"):
                    context += f"Resumen:\n{attachment.get('summary')}\n"
                
                if attachment.get("content"):
                    content = attachment.get("content", "")
                    if len(content) > 2000:
                        context += f"Contenido (primeras 2000 caracteres):\n{content[:2000]}...\n"
                    else:
                        context += f"Contenido:\n{content}\n"
        
        context += "\n" + "=" * 60 + "\n"
        
        logger.info(f"[v0] Contexto de archivos formateado: {len(context)} caracteres")
        return context
    
    @staticmethod
    def create_attachment_reference(attachment: Dict[str, Any]) -> str:
        """
        Crea una referencia corta al archivo para usar en el prompt
        """
        file_type = attachment.get("type") or attachment.get("file_type", "unknown")
        filename = attachment.get("filename", "Sin nombre")
        
        if file_type == "image":
            return f"imagen '{filename}'"
        elif file_type == "document":
            return f"documento '{filename}'"
        else:
            return f"archivo '{filename}'"
    
    @staticmethod
    def validate_attachments(attachments: List[Dict[str, Any]]) -> bool:
        """
        Valida que los archivos adjuntos tengan la estructura esperada
        """
        for attachment in attachments:
            has_type = "type" in attachment or "file_type" in attachment
            has_filename = "filename" in attachment
            
            if not (has_type and has_filename):
                logger.warning(f"[v0] Archivo adjunto con estructura invalida: {attachment}")
                return False
        
        logger.info(f"[v0] {len(attachments)} archivos adjuntos validados")
        return True
