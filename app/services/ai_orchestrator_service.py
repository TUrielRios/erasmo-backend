"""
Orquestador Central de IA - Integra todas las mejoras para maximo potencial
Coordina: Cache, Streaming, Presupuesto Adaptativo, Prompt Engineering, RAG
"""

from typing import Dict, List, Any, Optional, Tuple, AsyncGenerator
from app.services.advanced_cache_service import AdvancedCacheService
from app.services.streaming_optimizer_service import StreamingOptimizerService
from app.services.adaptive_budget_service import AdaptiveBudgetService
from app.services.prompt_engineering_service import PromptEngineeringService
from app.services.rag_intelligence_service import RAGIntelligenceService
from app.services.token_optimizer_service import TokenOptimizerService
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class AIOrchestrationService:
    """
    Servicio maestro que orquesta todas las capacidades de IA
    para maximo potencial, rendimiento y calidad
    """
    
    def __init__(self):
        self.cache_service = AdvancedCacheService()
        self.streaming_service = StreamingOptimizerService()
        self.budget_service = AdaptiveBudgetService()
        self.prompt_service = PromptEngineeringService()
        self.rag_service = RAGIntelligenceService()
        self.token_optimizer = TokenOptimizerService()
        
        logger.info("AI Orchestration Service inicializado con MAXIMO POTENCIAL")
    
    async def orchestrate_response_generation(
        self,
        user_message: str,
        session_id: str,
        user_id: int,
        company_id: int,
        project_id: Optional[int] = None,
        context: Optional[List[Dict]] = None,
        history: Optional[List[Dict]] = None,
        company_data: Optional[Dict] = None,
        instructions: Optional[List[Dict]] = None,
        require_analysis: bool = False
    ) -> Dict[str, Any]:
        """
        Orquesta el flujo completo de generacion de respuesta con todas las optimizaciones
        """
        
        logger.info(f"Orquestando respuesta para user {user_id}, session {session_id}")
        
        # 1. VERIFICAR CACHE
        cached_response = self.cache_service.get_cached_response(session_id, user_message)
        if cached_response:
            logger.info("Respuesta encontrada en cache - devolviendo cached")
            return {
                'source': 'cache',
                'response': cached_response,
                'cache_hit': True
            }
        
        # 2. CALCULAR PRESUPUESTO ADAPTATIVO
        history_length = len(history or [])
        adaptive_budget = self.budget_service.calculate_adaptive_budget(
            user_message,
            history_length,
            settings.MAX_CONTEXT_LENGTH,
            require_analysis
        )
        
        logger.info(f"Presupuesto adaptativo: {adaptive_budget['complexity_level']} - {adaptive_budget['total_allocated']} tokens")
        
        # 3. OPTIMIZAR CONTEXTO CON RAG + RERANKING
        if context:
            rag_result = self.rag_service.apply_rag_enhancement(user_message, context)
            optimized_context = rag_result['reranked_context']
            gap_analysis = self.rag_service.detect_knowledge_gaps(user_message, context)
            
            logger.info(f"RAG Enhancement: {gap_analysis['coverage_percentage']:.1f}% cobertura")
        else:
            optimized_context = []
            rag_result = None
            gap_analysis = None
        
        # 4. CONSTRUIR SYSTEM PROMPT ULTRA-OPTIMIZADO
        system_prompt = self.prompt_service.build_ultra_optimized_system_prompt(
            company_data.get('company_name', 'tu empresa') if company_data else 'tu empresa',
            company_data or {},
            instructions or [],
            {'id': project_id} if project_id else None
        )
        
        # 5. APLICAR TECNICAS DE PROMPT ENGINEERING
        techniques = []
        if adaptive_budget['complexity_level'] in ['complex', 'very_complex']:
            techniques = ['chain_of_thought', 'step_by_step']
        
        enhanced_user_message = user_message
        if techniques:
            enhanced_user_message = self.prompt_service.enhance_user_query(
                user_message,
                techniques
            )
        
        # Si tenemos RAG enhancement, usarlo
        if rag_result:
            enhanced_user_message = rag_result['enhanced_message']
        
        # 6. COMPRIMIR CONTEXTO E HISTORIAL AL PRESUPUESTO
        compressed_context = self.token_optimizer.compress_context(
            optimized_context,
            adaptive_budget['context_tokens']
        )
        
        compressed_history = self.token_optimizer._compress_history(
            history or [],
            adaptive_budget['history_tokens']
        )
        
        # 7. DETERMINAR MODO DE STREAMING
        should_stream = self.budget_service.should_use_streaming(
            adaptive_budget['response_tokens'],
            complexity_level=adaptive_budget['complexity_level']
        )
        
        logger.info(f"Streaming: {should_stream}, Tokens: {adaptive_budget['response_tokens']}")
        
        # 8. ESTIMAR CALIDAD
        quality_estimate = self.budget_service.estimate_response_quality(
            adaptive_budget['complexity_level'],
            adaptive_budget['total_allocated'],
            has_project_context=project_id is not None,
            has_custom_instructions=bool(instructions)
        )
        
        logger.info(f"Calidad estimada: {quality_estimate['quality_level']} ({quality_estimate['quality_score']})")
        
        # Retornar orquestacion completa
        return {
            'source': 'generation',
            'system_prompt': system_prompt,
            'user_message': enhanced_user_message,
            'context': compressed_context,
            'history': compressed_history,
            'budget': adaptive_budget,
            'quality_estimate': quality_estimate,
            'streaming_enabled': should_stream,
            'rag_analysis': {
                'enhancement': rag_result,
                'gaps': gap_analysis
            },
            'cache_stats': self.cache_service.get_cache_stats()
        }
    
    def cache_generated_response(
        self,
        session_id: str,
        user_message: str,
        response: Dict[str, Any]
    ):
        """
        Almacena respuesta generada en cache para futuros usos
        """
        self.cache_service.cache_response(
            session_id,
            user_message,
            response
        )
    
    def get_orchestration_metrics(self) -> Dict[str, Any]:
        """
        Obtiene metricas de orquestacion para monitoreo
        """
        return {
            'cache_stats': self.cache_service.get_cache_stats(),
            'token_optimization_enabled': settings.ENABLE_TOKEN_OPTIMIZATION,
            'advanced_caching_enabled': settings.ENABLE_ADVANCED_CACHING,
            'streaming_optimization_enabled': settings.ENABLE_STREAMING_OPTIMIZATION,
            'rag_intelligence_enabled': settings.ENABLE_RAAG,
            'context_reranking_enabled': settings.ENABLE_CONTEXT_RERANKING,
            'response_refinement_enabled': settings.ENABLE_RESPONSE_REFINEMENT,
            'max_context_tokens': settings.MAX_CONTEXT_LENGTH,
            'max_response_tokens': settings.MAX_RESPONSE_TOKENS,
            'conversation_memory_size': settings.CONVERSATION_MEMORY_SIZE
        }
