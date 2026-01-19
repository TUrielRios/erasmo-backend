"""
Servicio para validar que las respuestas cumplan con longitud minima
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class ResponseValidatorService:
    """Valida que las respuestas cumplan con los requisitos de longitud"""
    
    def __init__(self, min_tokens: int = None, max_tokens: int = None):
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
    
    def validate_response_length(self, response: str) -> Tuple[bool, str, int]:
        """
        Valida que la respuesta cumpla con la longitud minima y maxima
        
        Returns:
            (is_valid, message, token_estimate)
        """
        response_length = len(response)
        # Rough estimate: 1 token  4 characters
        estimated_tokens = int(response_length / 4)
        
        if self.min_tokens and estimated_tokens < self.min_tokens:
            deficit_tokens = self.min_tokens - estimated_tokens
            deficit_chars = deficit_tokens * 4
            message = f"[WARN] Respuesta muy corta: {estimated_tokens} tokens (minimo: {self.min_tokens}). Falta: {deficit_tokens} tokens ({deficit_chars} caracteres)"
            return False, message, estimated_tokens

        if self.max_tokens and estimated_tokens > self.max_tokens:
            excess_tokens = estimated_tokens - self.max_tokens
            message = f"[WARN] Respuesta muy larga: {estimated_tokens} tokens (maximo: {self.max_tokens}). Excede por: {excess_tokens} tokens"
            return False, message, estimated_tokens
            
        return True, f"Respuesta valida: {estimated_tokens} tokens", estimated_tokens
    
    def log_response_quality(self, response: str, session_id: str, user_id: int):
        """Registra la calidad de la respuesta en los logs"""
        is_valid, message, tokens = self.validate_response_length(response)
        
        if is_valid:
            logger.info(f"[OK] [RESPONSE QUALITY] Session {session_id} | User {user_id} | {message}")
        else:
            logger.warning(f"[WARN] [RESPONSE QUALITY] Session {session_id} | User {user_id} | {message}")
        
        return is_valid, tokens
