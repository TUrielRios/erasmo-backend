"""
Servicio para generar embeddings usando OpenAI
"""

import openai
from typing import List, Dict, Any, Optional
import asyncio
import logging
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        """
        Inicializa el servicio de embeddings
        """
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL or "text-embedding-3-small"
        self.max_tokens = 8000  # Límite aproximado para el modelo de embedding
        
        # Inicializar tokenizer para contar tokens
        try:
            self.encoding = tiktoken.encoding_for_model("text-embedding-3-small")
        except KeyError:
            # Fallback si el modelo no está en tiktoken
            self.encoding = tiktoken.get_encoding("cl100k_base")
        
        logger.info(f"EmbeddingService inicializado con modelo: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Genera embedding para un texto individual
        
        Args:
            text: Texto para convertir a embedding
            
        Returns:
            Lista de floats representando el vector de embedding
        """
        try:
            # Preprocesar texto
            cleaned_text = self._clean_text(text)
            
            # Verificar límite de tokens
            if self._count_tokens(cleaned_text) > self.max_tokens:
                cleaned_text = self._truncate_text(cleaned_text, self.max_tokens)
                logger.warning(f"Texto truncado a {self.max_tokens} tokens")
            
            # Generar embedding
            response = await self.client.embeddings.create(
                input=cleaned_text,
                model=self.model
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Embedding generado: dimensión {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise

    async def generate_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Genera embeddings para múltiples textos en lotes
        
        Args:
            texts: Lista de textos
            batch_size: Tamaño del lote para procesamiento
            
        Returns:
            Lista de embeddings correspondientes
        """
        try:
            embeddings = []
            
            # Procesar en lotes para evitar límites de API
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                # Limpiar y truncar textos del lote
                cleaned_batch = []
                for text in batch:
                    cleaned = self._clean_text(text)
                    if self._count_tokens(cleaned) > self.max_tokens:
                        cleaned = self._truncate_text(cleaned, self.max_tokens)
                    cleaned_batch.append(cleaned)
                
                # Generar embeddings para el lote
                batch_embeddings = await self._generate_batch_embeddings(cleaned_batch)
                embeddings.extend(batch_embeddings)
                
                logger.info(f"Procesado lote {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
                
                # Pequeña pausa entre lotes para evitar rate limiting
                await asyncio.sleep(0.1)
            
            logger.info(f"Generados {len(embeddings)} embeddings exitosamente")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generando embeddings en lote: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings para un lote específico
        """
        response = await self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        
        # Extraer embeddings manteniendo el orden
        embeddings = [data.embedding for data in response.data]
        return embeddings

    def _clean_text(self, text: str) -> str:
        """
        Limpia y preprocesa el texto para embedding
        """
        if not text:
            return ""
        
        # Remover caracteres de control y espacios excesivos
        cleaned = ' '.join(text.split())
        
        # Remover caracteres especiales problemáticos
        cleaned = cleaned.replace('\x00', '')  # NULL characters
        cleaned = cleaned.replace('\ufeff', '')  # BOM
        
        return cleaned

    def _count_tokens(self, text: str) -> int:
        """
        Cuenta tokens en un texto usando tiktoken
        """
        try:
            return len(self.encoding.encode(text))
        except Exception:
            # Fallback: aproximación por caracteres
            return len(text) // 4

    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """
        Trunca texto al límite de tokens especificado
        """
        try:
            tokens = self.encoding.encode(text)
            if len(tokens) <= max_tokens:
                return text
            
            # Truncar tokens y decodificar
            truncated_tokens = tokens[:max_tokens]
            return self.encoding.decode(truncated_tokens)
            
        except Exception:
            # Fallback: truncar por caracteres (aproximado)
            approx_chars = max_tokens * 4
            return text[:approx_chars]

    async def calculate_similarity(
        self, 
        embedding1: List[float], 
        embedding2: List[float]
    ) -> float:
        """
        Calcula similaridad coseno entre dos embeddings
        
        Returns:
            Valor de similaridad entre 0 y 1
        """
        try:
            import numpy as np
            
            # Convertir a arrays numpy
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calcular similaridad coseno
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Convertir de [-1, 1] a [0, 1]
            normalized_similarity = (similarity + 1) / 2
            
            return float(normalized_similarity)
            
        except Exception as e:
            logger.error(f"Error calculando similaridad: {e}")
            return 0.0

    async def find_most_similar(
        self, 
        query_embedding: List[float], 
        candidate_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Encuentra los embeddings más similares a una consulta
        
        Returns:
            Lista de diccionarios con índice y score de similaridad
        """
        try:
            similarities = []
            
            for i, candidate in enumerate(candidate_embeddings):
                similarity = await self.calculate_similarity(query_embedding, candidate)
                similarities.append({
                    'index': i,
                    'similarity_score': similarity
                })
            
            # Ordenar por similaridad descendente
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Retornar top_k resultados
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error encontrando similares: {e}")
            return []

    async def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del servicio de embeddings
        """
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "status": "healthy",
            "encoding": "tiktoken" if hasattr(self, 'encoding') else "fallback"
        }

# Utilidad para calcular costo aproximado
def estimate_embedding_cost(
    num_tokens: int, 
    model: str = "text-embedding-3-small"
) -> float:
    """
    Estima el costo de generar embeddings
    
    Args:
        num_tokens: Número de tokens a procesar
        model: Modelo de embedding utilizado
        
    Returns:
        Costo estimado en USD
    """
    # Precios aproximados por 1K tokens (actualizar según pricing de OpenAI)
    pricing = {
        "text-embedding-3-small": 0.00002,  # $0.00002 per 1K tokens
        "text-embedding-3-large": 0.00013,  # $0.00013 per 1K tokens
        "text-embedding-ada-002": 0.0001,   # $0.0001 per 1K tokens (legacy)
    }
    
    cost_per_1k = pricing.get(model, 0.00002)  # Default a small model
    return (num_tokens / 1000) * cost_per_1k