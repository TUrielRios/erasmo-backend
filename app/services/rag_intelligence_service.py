"""
Servicio de Inteligencia RAG Avanzada (Retrieval Augmented Analysis Generation)
Maximiza el potencial de la IA combinando recuperación inteligente con generación superior
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

class RAGIntelligenceService:
    """
    Sistema RAG avanzado que combina:
    - Recuperación inteligente de contexto
    - Análisis profundo de relevancia
    - Generación aumentada con conocimiento contextual
    """
    
    def __init__(self):
        self.retrieval_cache: Dict[str, List[Dict]] = {}
        self.relevance_scores: Dict[str, float] = {}
        self.analysis_patterns: Dict[str, List[str]] = {}
    
    def hybrid_context_retrieval(
        self,
        query: str,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        knowledge_base: List[Dict],
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Recuperación híbrida: combina búsqueda vectorial + keyword + conocimiento base
        """
        combined_results = []
        seen_ids = set()
        
        # Asignar scores iniciales
        for result in vector_results:
            result_id = result.get('id', f"vector_{len(combined_results)}")
            if result_id not in seen_ids:
                result['retrieval_score'] = result.get('score', 0.5) * 0.6  # Peso 60%
                result['source_type'] = 'vector_search'
                combined_results.append(result)
                seen_ids.add(result_id)
        
        # Agregar keyword results
        for result in keyword_results:
            result_id = result.get('id', f"keyword_{len(combined_results)}")
            if result_id not in seen_ids:
                result['retrieval_score'] = result.get('score', 0.4) * 0.3  # Peso 30%
                result['source_type'] = 'keyword_search'
                combined_results.append(result)
                seen_ids.add(result_id)
            else:
                # Aumentar score si aparece en ambas búsquedas
                for item in combined_results:
                    if item.get('id') == result_id:
                        item['retrieval_score'] += 0.15
        
        # Agregar conocimiento base relevante
        for doc in knowledge_base[:10]:
            doc_id = doc.get('id', f"kb_{len(combined_results)}")
            if doc_id not in seen_ids:
                relevance = self._calculate_doc_relevance(query, doc)
                if relevance > 0.4:
                    doc['retrieval_score'] = relevance * 0.2  # Peso 20%
                    doc['source_type'] = 'knowledge_base'
                    combined_results.append(doc)
                    seen_ids.add(doc_id)
        
        # Ordenar por relevancia combinada
        combined_results.sort(
            key=lambda x: (x.get('retrieval_score', 0), x.get('priority', 5)),
            reverse=True
        )
        
        return combined_results[:top_k]
    
    def _calculate_doc_relevance(self, query: str, doc: Dict) -> float:
        """
        Calcula relevancia de un documento respecto a la query
        """
        query_words = set(query.lower().split())
        doc_content = doc.get('content', '') + doc.get('title', '')
        doc_words = set(doc_content.lower().split())
        
        if not query_words or not doc_words:
            return 0.0
        
        # Similarity basado en overlap de palabras
        overlap = len(query_words.intersection(doc_words))
        max_possible = max(len(query_words), len(doc_words))
        
        return min(overlap / max_possible, 1.0)
    
    def rerank_context_by_relevance(
        self,
        query: str,
        context: List[Dict[str, Any]],
        rerank_depth: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Re-rankea contexto por relevancia profunda a la query
        """
        ranked = []
        
        for item in context[:rerank_depth]:
            content = item.get('content', '')
            
            # Calcular múltiples dimensiones de relevancia
            relevance_scores = {
                'keyword_overlap': self._calculate_keyword_overlap(query, content),
                'semantic_similarity': item.get('relevance_score', 0.5),
                'content_completeness': min(len(content) / 1000, 1.0),
                'source_priority': self._get_source_priority(item.get('source_type', 'general'))
            }
            
            # Score combinado con pesos
            combined_score = (
                relevance_scores['keyword_overlap'] * 0.3 +
                relevance_scores['semantic_similarity'] * 0.4 +
                relevance_scores['content_completeness'] * 0.15 +
                relevance_scores['source_priority'] * 0.15
            )
            
            item['rerank_score'] = combined_score
            item['relevance_breakdown'] = relevance_scores
            ranked.append(item)
        
        ranked.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
        
        return ranked
    
    def _calculate_keyword_overlap(self, query: str, content: str) -> float:
        """
        Calcula overlap de keywords entre query y contenido
        """
        query_words = set(w.lower() for w in query.split() if len(w) > 3)
        content_words = set(w.lower() for w in content.split() if len(w) > 3)
        
        if not query_words:
            return 0.5
        
        overlap = len(query_words.intersection(content_words))
        return min(overlap / len(query_words), 1.0)
    
    def _get_source_priority(self, source_type: str) -> float:
        """
        Obtiene prioridad basada en tipo de fuente
        """
        priorities = {
            'project_document': 1.0,
            'vector_search': 0.85,
            'keyword_search': 0.7,
            'knowledge_base': 0.75,
            'general': 0.5
        }
        return priorities.get(source_type, 0.5)
    
    def generate_context_summary(
        self,
        context: List[Dict[str, Any]],
        max_tokens: int = 1000
    ) -> str:
        """
        Genera resumen de contexto para inyección en prompt
        """
        summary = "CONTEXTO DISPONIBLE:\n\n"
        
        total_length = 0
        for i, item in enumerate(context[:10], 1):
            source = item.get('source', 'desconocido')
            content = item.get('content', '')[:300]
            relevance = item.get('rerank_score', item.get('relevance_score', 0))
            
            item_text = f"{i}. [{source}] (Relevancia: {relevance:.2f})\n{content}...\n\n"
            
            if total_length + len(item_text.split()) < max_tokens:
                summary += item_text
                total_length += len(item_text.split())
            else:
                break
        
        return summary
    
    def apply_rag_enhancement(
        self,
        user_message: str,
        context: List[Dict[str, Any]],
        analysis_type: str = "standard"
    ) -> Dict[str, Any]:
        """
        Aplica mejoras RAG al mensaje para máximo potencial de respuesta
        """
        reranked_context = self.rerank_context_by_relevance(user_message, context)
        context_summary = self.generate_context_summary(reranked_context)
        
        enhanced_message = f"""{context_summary}

PREGUNTA/TAREA: {user_message}

INSTRUCCIONES DE ANÁLISIS:
1. Usa PRIMERO el contexto disponible para informar tu respuesta
2. Si el contexto no cubre todo, combina con conocimiento general
3. Cita tus fuentes cuando corresponda
4. Señala si hay lagunas en el contexto
5. Proporciona análisis completo y bien fundamentado
"""
        
        return {
            'enhanced_message': enhanced_message,
            'context_summary': context_summary,
            'reranked_context': reranked_context,
            'total_context_items': len(reranked_context),
            'average_relevance': sum(
                item.get('rerank_score', 0) for item in reranked_context
            ) / len(reranked_context) if reranked_context else 0
        }
    
    def detect_knowledge_gaps(
        self,
        user_message: str,
        context: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detecta lagunas de conocimiento en el contexto disponible
        """
        context_keywords = set()
        for item in context:
            words = item.get('content', '').lower().split()
            context_keywords.update(words)
        
        query_keywords = set(w.lower() for w in user_message.split() if len(w) > 3)
        
        covered_keywords = query_keywords.intersection(context_keywords)
        missing_keywords = query_keywords - context_keywords
        
        coverage_percentage = (len(covered_keywords) / len(query_keywords) * 100) if query_keywords else 100
        
        return {
            'coverage_percentage': coverage_percentage,
            'covered_keywords': list(covered_keywords),
            'missing_keywords': list(missing_keywords),
            'has_gaps': coverage_percentage < 70,
            'recommendation': self._gap_recommendation(coverage_percentage)
        }
    
    def _gap_recommendation(self, coverage: float) -> str:
        """
        Proporciona recomendación basada en cobertura
        """
        if coverage >= 90:
            return "Contexto excelente. Procede con respuesta de alta confianza."
        elif coverage >= 70:
            return "Contexto adecuado. Combina conocimiento contextual con análisis general."
        elif coverage >= 50:
            return "Contexto parcial. Señala asunciones basadas en general knowledge."
        else:
            return "Contexto limitado. Busca información adicional o señala claramente incertidumbres."
