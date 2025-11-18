"""
Servicio avanzado de caché para contexto y respuestas
Implementa múltiples estrategias de caché para máximo rendimiento y eficiencia
"""

import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
from app.core.config import settings

class AdvancedCacheService:
    """
    Sistema de caché multi-nivel para contexto, respuestas y análisis
    Optimiza reutilización de contexto y acelera respuestas similares
    """
    
    def __init__(self):
        self.context_cache: Dict[str, Dict[str, Any]] = {}
        self.response_cache: Dict[str, Dict[str, Any]] = {}
        self.semantic_cache: Dict[str, List[str]] = {}  # Para búsquedas semánticas
        self.cache_stats = {
            'context_hits': 0,
            'context_misses': 0,
            'response_hits': 0,
            'response_misses': 0,
            'total_cached': 0
        }
    
    def _generate_context_key(self, company_id: int, project_id: Optional[int], message: str) -> str:
        """
        Genera clave de caché única para contexto basada en compañía, proyecto y mensaje
        """
        key_data = f"{company_id}:{project_id}:{message[:100]}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _generate_response_key(self, session_id: str, message: str) -> str:
        """
        Genera clave de caché única para respuestas
        """
        key_data = f"{session_id}:{message}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_cached_context(self, company_id: int, project_id: Optional[int], message: str) -> Optional[List[Dict[str, Any]]]:
        """
        Obtiene contexto del caché si existe y es válido
        """
        key = self._generate_context_key(company_id, project_id, message)
        
        if key in self.context_cache:
            cached = self.context_cache[key]
            # Verificar expiración
            if datetime.now() < cached['expires_at']:
                self.cache_stats['context_hits'] += 1
                return cached['context']
            else:
                # Limpiar entrada expirada
                del self.context_cache[key]
        
        self.cache_stats['context_misses'] += 1
        return None
    
    def cache_context(self, company_id: int, project_id: Optional[int], message: str, context: List[Dict[str, Any]]):
        """
        Almacena contexto en caché con TTL
        """
        key = self._generate_context_key(company_id, project_id, message)
        
        self.context_cache[key] = {
            'context': context,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=settings.CACHE_TTL_SECONDS),
            'hits': 0,
            'size_bytes': len(json.dumps(context))
        }
        self.cache_stats['total_cached'] += 1
    
    def get_cached_response(self, session_id: str, message: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene respuesta en caché si existe
        """
        key = self._generate_response_key(session_id, message)
        
        if key in self.response_cache:
            cached = self.response_cache[key]
            if datetime.now() < cached['expires_at']:
                self.cache_stats['response_hits'] += 1
                cached['hits'] += 1
                return cached['response']
            else:
                del self.response_cache[key]
        
        self.cache_stats['response_misses'] += 1
        return None
    
    def cache_response(self, session_id: str, message: str, response: Dict[str, Any]):
        """
        Almacena respuesta en caché con TTL más largo
        """
        key = self._generate_response_key(session_id, message)
        
        self.response_cache[key] = {
            'response': response,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=settings.CACHE_TTL_SECONDS * 2),  # 2x TTL
            'hits': 0,
            'size_bytes': len(json.dumps(response))
        }
    
    def find_similar_cached_response(self, message: str, threshold: float = 0.85) -> Optional[Dict[str, Any]]:
        """
        Busca respuestas en caché similares usando similitud de caracteres
        Útil para preguntas muy similares
        """
        from difflib import SequenceMatcher
        
        best_match = None
        best_score = threshold
        
        for key, cached in self.response_cache.items():
            if datetime.now() < cached['expires_at']:
                # Obtener mensaje del contenido cacheado
                similarity = SequenceMatcher(None, message, key).ratio()
                if similarity > best_score:
                    best_score = similarity
                    best_match = cached['response']
        
        return best_match if best_match else None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché
        """
        total_hits = self.cache_stats['context_hits'] + self.cache_stats['response_hits']
        total_requests = total_hits + self.cache_stats['context_misses'] + self.cache_stats['response_misses']
        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0
        
        context_size = sum(c['size_bytes'] for c in self.context_cache.values())
        response_size = sum(c['size_bytes'] for c in self.response_cache.values())
        
        return {
            'context_hits': self.cache_stats['context_hits'],
            'context_misses': self.cache_stats['context_misses'],
            'response_hits': self.cache_stats['response_hits'],
            'response_misses': self.cache_stats['response_misses'],
            'total_cached': self.cache_stats['total_cached'],
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size_mb': round((context_size + response_size) / (1024 * 1024), 2),
            'context_entries': len(self.context_cache),
            'response_entries': len(self.response_cache)
        }
    
    def cleanup_expired(self):
        """
        Limpia entradas expiradas del caché
        Debería ejecutarse periódicamente
        """
        now = datetime.now()
        
        expired_context = [k for k, v in self.context_cache.items() if now >= v['expires_at']]
        expired_response = [k for k, v in self.response_cache.items() if now >= v['expires_at']]
        
        for key in expired_context:
            del self.context_cache[key]
        
        for key in expired_response:
            del self.response_cache[key]
        
        return len(expired_context) + len(expired_response)
