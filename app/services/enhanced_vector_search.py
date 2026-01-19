"""
Servicio mejorado de busqueda vectorial con multiples estrategias
Combina busqueda semantica, relevancia y recency para mejor recuperacion de contexto
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import asyncio

class EnhancedVectorSearchService:
    """
    Servicio avanzado de busqueda vectorial con:
    - Busqueda semantica con Pinecone
    - Reranking de resultados
    - Filtrado por recency
    - Deduplicacion inteligente
    """
    
    def __init__(self, vector_store=None):
        self.vector_store = vector_store
        self.search_cache: Dict[str, List[Dict]] = {}
    
    async def advanced_similarity_search(
        self,
        query: str,
        company_id: Optional[int] = None,
        project_id: Optional[int] = None,
        top_k: int = 25,
        min_score: float = 0.3,
        filter_by_recency: bool = False,
        recency_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Realiza busqueda avanzada con multiples criterios
        """
        if not self.vector_store:
            return []
        
        try:
            # Busqueda semantica base
            semantic_results = await self.vector_store.similarity_search(
                query,
                top_k=top_k * 2,  # Obtener mas para reranking
                company_id=company_id,
                project_id=project_id
            )
            
            # Filtrar por puntuacion minima
            filtered_results = [
                r for r in semantic_results 
                if r.get('score', 0.0) >= min_score
            ]
            
            # Aplicar filtro de recency si se solicita
            if filter_by_recency:
                cutoff_date = datetime.now() - timedelta(days=recency_days)
                filtered_results = [
                    r for r in filtered_results
                    if self._check_recency(r, cutoff_date)
                ]
            
            # Reranking y deduplicacion
            reranked = self._rerank_results(filtered_results, query)
            deduplicated = self._deduplicate_results(reranked)
            
            # Retornar top_k resultados
            return deduplicated[:top_k]
            
        except Exception as e:
            print(f"[ERR] Error en busqueda avanzada: {e}")
            return []
    
    def _rerank_results(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Reranking de resultados usando multiples senales
        """
        query_terms = set(query.lower().split())
        
        for result in results:
            # Puntuacion base (de busqueda semantica)
            base_score = result.get('score', 0.5)
            
            # Bonus por relevancia de palabras clave
            content = result.get('content', '').lower()
            term_matches = len([t for t in query_terms if t in content])
            relevance_bonus = (term_matches / len(query_terms)) * 0.2 if query_terms else 0
            
            # Bonus por categoria (proyecto > empresa > general)
            category = result.get('category', '')
            category_bonus = {
                'project_vector_search': 0.15,
                'project_knowledge': 0.12,
                'company_vector_search': 0.08,
                'company_knowledge': 0.05,
                'general': 0.0
            }.get(category, 0.0)
            
            # Bonus por recency (documentos recientes mas importantes)
            recency_bonus = self._calculate_recency_bonus(result)
            
            # Puntuacion final
            final_score = min(base_score + relevance_bonus + category_bonus + recency_bonus, 1.0)
            result['final_score'] = final_score
        
        # Ordenar por puntuacion final
        results.sort(key=lambda x: x.get('final_score', 0.0), reverse=True)
        return results
    
    def _deduplicate_results(
        self,
        results: List[Dict[str, Any]],
        similarity_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """
        Elimina resultados muy similares (duplicados)
        """
        deduplicated = []
        seen_contents = []
        
        for result in results:
            content = result.get('content', '')
            
            # Verificar si es similar a algo ya visto
            is_duplicate = False
            for seen_content in seen_contents:
                similarity = self._calculate_text_similarity(content, seen_content)
                if similarity > similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(result)
                seen_contents.append(content)
        
        return deduplicated
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similitud basica entre dos textos
        Usa Jaccard similarity sobre palabras
        """
        words1 = set(text1.lower().split()[:100])  # Limitar a primeras 100 palabras
        words2 = set(text2.lower().split()[:100])
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_recency_bonus(self, result: Dict[str, Any]) -> float:
        """
        Calcula bonus basado en recency del documento
        """
        try:
            created_at = result.get('created_at')
            if not created_at:
                return 0.0
            
            # Si created_at es string, convertir
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            
            days_old = (datetime.now() - created_at).days
            
            # Bonus decreciente: nuevos documentos get 0.1, antiguos get 0.0
            if days_old < 7:
                return 0.1
            elif days_old < 30:
                return 0.05
            else:
                return 0.0
        except Exception:
            return 0.0
    
    def _check_recency(self, result: Dict[str, Any], cutoff_date: datetime) -> bool:
        """
        Verifica si un resultado es reciente respecto a cutoff_date
        """
        try:
            created_at = result.get('created_at')
            if not created_at:
                return True
            
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            
            return created_at >= cutoff_date
        except Exception:
            return True
    
    async def hybrid_search(
        self,
        query: str,
        company_id: Optional[int] = None,
        project_id: Optional[int] = None,
        top_k: int = 25,
        min_score: float = 0.3  # Added min_score parameter
    ) -> List[Dict[str, Any]]:
        """
        Busqueda hibrida: combina semantica + termino exacto
        Mas robusto que solo semantica
        """
        try:
            # Busqueda semantica avanzada con todos los parametros
            semantic_results = await self.advanced_similarity_search(
                query,
                company_id=company_id,
                project_id=project_id,
                top_k=top_k,
                min_score=min_score  # Pass min_score to advanced_similarity_search
            )
            
            # Busqueda por terminos exactos (bonus)
            query_terms = query.lower().split()
            for result in semantic_results:
                content = result.get('content', '').lower()
                term_count = sum(1 for term in query_terms if term in content)
                
                # Si contiene muchos terminos exactos, aumentar score
                if term_count >= len(query_terms) * 0.7:
                    result['final_score'] = min(result.get('final_score', 0.5) + 0.2, 1.0)
            
            # Re-ordenar despues de ajustes
            semantic_results.sort(key=lambda x: x.get('final_score', 0.0), reverse=True)
            
            return semantic_results[:top_k]
        
        except Exception as e:
            print(f"[ERR] Error en hybrid_search: {e}")
            return []
