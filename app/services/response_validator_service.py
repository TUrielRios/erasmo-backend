"""
Servicio para validar que las respuestas cumplan con longitud mínima
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class ResponseValidatorService:
    """Valida que las respuestas cumplan con los requisitos de longitud"""
    
    def __init__(self, min_tokens: int = 1500):
        self.min_tokens = min_tokens
        # Rough estimate: 1 token ≈ 4 characters
        self.min_characters = min_tokens * 4
    
    def validate_response_length(self, response: str) -> Tuple[bool, str, int]:
        """
        Valida que la respuesta cumpla con la longitud mínima
        
        Returns:
            (is_valid, message, token_estimate)
        """
        response_length = len(response)
        estimated_tokens = int(response_length / 4)
        
        if estimated_tokens >= self.min_tokens:
            return True, f"Respuesta válida: {estimated_tokens} tokens", estimated_tokens
        
        # Si no cumple, reportar déficit
        deficit_tokens = self.min_tokens - estimated_tokens
        deficit_chars = deficit_tokens * 4
        
        message = f"⚠️ Respuesta muy corta: {estimated_tokens} tokens (mínimo: {self.min_tokens}). Falta: {deficit_tokens} tokens ({deficit_chars} caracteres)"
        
        return False, message, estimated_tokens
    
    def log_response_quality(self, response: str, session_id: str, user_id: int):
        """Registra la calidad de la respuesta en los logs"""
        is_valid, message, tokens = self.validate_response_length(response)
        
        if is_valid:
            logger.info(f"✅ [RESPONSE QUALITY] Session {session_id} | User {user_id} | {message}")
        else:
            logger.warning(f"⚠️ [RESPONSE QUALITY] Session {session_id} | User {user_id} | {message}")
        
        return is_valid, tokens
