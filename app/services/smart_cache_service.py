"""
Sistema inteligente de cache para respuestas y contexto
Mejora velocidad de respuesta sin sacrificar relevancia
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from functools import lru_cache
import asyncio

class SmartCacheService:
    """
    Cache inteligente que:
    - Almacena respuestas completas para consultas similares
    - Cache de embeddings para busquedas vectoriales
    - Cache de contexto para conversaciones
    - Invalidacion automatica basada en tiempo y cambios
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        self.response_cache: Dict[str, Dict[str, Any]] = {}
        self.context_cache: Dict[str, Dict[str, Any]] = {}
        self.embedding_cache: Dict[str, List[float]] = {}
        self.ttl_seconds = ttl_seconds
        self.cache_hits = 0
        self.cache_misses = 0
    
    def _generate_cache_key(self, data: str) -> str:
        """
        Genera una clave de cache unica basada en hash
        """
        return hashlib.md5(data.encode()).hexdigest()
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """
        Verifica si un cache sigue siendo valido
        """
        age = (datetime.now() - timestamp).total_seconds()
        return age < self.ttl_seconds
    
    def cache_response(
        self,
        query: str,
        response: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Guarda una respuesta en cache
        """
        cache_key = self._generate_cache_key(query)
        
        self.response_cache[cache_key] = {
            "query": query,
            "response": response,
            "session_id": session_id,
            "timestamp": datetime.now(),
            "metadata": metadata or {},
            "accessed_count": 0
        }
        
        return cache_key
    
    def get_cached_response(self, query: str) -> Optional[str]:
        """
        Obtiene una respuesta del cache si existe y es valida
        """
        cache_key = self._generate_cache_key(query)
        
        if cache_key in self.response_cache:
            cache_entry = self.response_cache[cache_key]
            
            if self._is_cache_valid(cache_entry["timestamp"]):
                cache_entry["accessed_count"] += 1
                self.cache_hits += 1
                print(f"[OK] Cache hit for query: {query[:50]}...")
                return cache_entry["response"]
            else:
                # Expiro, eliminar
                del self.response_cache[cache_key]
        
        self.cache_misses += 1
        return None
    
    def find_similar_cached_responses(
        self,
        query: str,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[str, float]]:
        """
        Encuentra respuestas en cache que son similares a la consulta
        Retorna lista de (response, similarity_score)
        """
        query_words = set(query.lower().split())
        similar_responses = []
        
        for cache_entry in self.response_cache.values():
            if not self._is_cache_valid(cache_entry["timestamp"]):
                continue
            
            cached_query_words = set(cache_entry["query"].lower().split())
            
            # Calcular similitud Jaccard
            intersection = len(query_words.intersection(cached_query_words))
            union = len(query_words.union(cached_query_words))
            similarity = intersection / union if union > 0 else 0.0
            
            if similarity >= similarity_threshold:
                similar_responses.append((cache_entry["response"], similarity))
        
        # Ordenar por similitud
        similar_responses.sort(key=lambda x: x[1], reverse=True)
        return similar_responses
    
    def cache_context(
        self,
        session_id: str,
        context: List[Dict[str, Any]],
        conversation_state: Dict[str, Any]
    ) -> None:
        """
        Guarda contexto de conversacion en cache
        """
        cache_key = f"context_{session_id}"
        
        self.context_cache[cache_key] = {
            "session_id": session_id,
            "context": context,
            "conversation_state": conversation_state,
            "timestamp": datetime.now(),
            "last_accessed": datetime.now()
        }
    
    def get_cached_context(
        self,
        session_id: str
    ) -> Optional[Tuple[List[Dict[str, Any]], Dict[str, Any]]]:
        """
        Obtiene contexto cacheado para una sesion
        Retorna (context, conversation_state) o None
        """
        cache_key = f"context_{session_id}"
        
        if cache_key in self.context_cache:
            cache_entry = self.context_cache[cache_key]
            
            if self._is_cache_valid(cache_entry["timestamp"]):
                cache_entry["last_accessed"] = datetime.now()
                return cache_entry["context"], cache_entry["conversation_state"]
            else:
                del self.context_cache[cache_key]
        
        return None
    
    def invalidate_session_cache(self, session_id: str) -> None:
        """
        Invalida todo el cache asociado a una sesion
        """
        cache_key = f"context_{session_id}"
        if cache_key in self.context_cache:
            del self.context_cache[cache_key]
        
        # Tambien limpiar respuestas cacheadas de esta sesion
        keys_to_delete = []
        for cache_key, entry in self.response_cache.items():
            if entry.get("session_id") == session_id:
                keys_to_delete.append(cache_key)
        
        for cache_key in keys_to_delete:
            del self.response_cache[cache_key]
    
    def cache_embeddings(
        self,
        text: str,
        embeddings: List[float]
    ) -> None:
        """
        Guarda embeddings en cache
        """
        cache_key = self._generate_cache_key(text)
        self.embedding_cache[cache_key] = embeddings
    
    def get_cached_embeddings(self, text: str) -> Optional[List[float]]:
        """
        Obtiene embeddings del cache
        """
        cache_key = self._generate_cache_key(text)
        return self.embedding_cache.get(cache_key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retorna estadisticas del cache
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),
            "cached_responses": len(self.response_cache),
            "cached_contexts": len(self.context_cache),
            "cached_embeddings": len(self.embedding_cache),
            "total_cached_items": len(self.response_cache) + len(self.context_cache) + len(self.embedding_cache)
        }
    
    def cleanup_expired_cache(self) -> Dict[str, int]:
        """
        Limpia elementos expirados del cache
        Retorna cuantos elementos se eliminaron
        """
        deleted_count = {
            "responses": 0,
            "contexts": 0,
            "embeddings": 0
        }
        
        # Limpiar respuestas expiradas
        keys_to_delete = []
        for cache_key, entry in self.response_cache.items():
            if not self._is_cache_valid(entry["timestamp"]):
                keys_to_delete.append(cache_key)
        
        for cache_key in keys_to_delete:
            del self.response_cache[cache_key]
            deleted_count["responses"] += 1
        
        # Limpiar contextos expirados
        keys_to_delete = []
        for cache_key, entry in self.context_cache.items():
            if not self._is_cache_valid(entry["timestamp"]):
                keys_to_delete.append(cache_key)
        
        for cache_key in keys_to_delete:
            del self.context_cache[cache_key]
            deleted_count["contexts"] += 1
        
        # Los embeddings pueden tener mas TTL
        # Por ahora no los limpian pero podrian tener su propio TTL
        
        return deleted_count
