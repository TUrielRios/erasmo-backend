"""
Endpoint para monitoreo y control de optimizaciones de IA
Proporciona visibilidad en el sistema de orquestacion
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.ai_orchestrator_service import AIOrchestrationService
from app.services.advanced_cache_service import AdvancedCacheService
from app.services.adaptive_budget_service import AdaptiveBudgetService
from app.core.config import settings

router = APIRouter(prefix="/optimization", tags=["ai_optimization"])

orchestrator = AIOrchestrationService()
cache_service = AdvancedCacheService()
budget_service = AdaptiveBudgetService()

@router.get("/metrics")
async def get_ai_optimization_metrics():
    """
    Obtiene metricas de optimizacion del sistema de IA
    Incluye: cache, presupuesto, streaming, RAG
    """
    try:
        metrics = orchestrator.get_orchestration_metrics()
        
        return {
            "status": "success",
            "metrics": metrics,
            "system_configuration": {
                "model": settings.OPENAI_MODEL,
                "max_context_length": settings.MAX_CONTEXT_LENGTH,
                "max_response_tokens": settings.MAX_RESPONSE_TOKENS,
                "conversation_memory": settings.CONVERSATION_MEMORY_SIZE,
                "cache_ttl_seconds": settings.CACHE_TTL_SECONDS,
                "features_enabled": {
                    "advanced_caching": settings.ENABLE_ADVANCED_CACHING,
                    "streaming_optimization": settings.ENABLE_STREAMING_OPTIMIZATION,
                    "token_optimization": settings.ENABLE_TOKEN_OPTIMIZATION,
                    "rag_intelligence": settings.ENABLE_RAAG,
                    "context_reranking": settings.ENABLE_CONTEXT_RERANKING,
                    "response_refinement": settings.ENABLE_RESPONSE_REFINEMENT
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo metricas: {str(e)}"
        )

@router.get("/cache-stats")
async def get_cache_statistics():
    """
    Obtiene estadisticas detalladas del cache
    """
    try:
        stats = cache_service.get_cache_stats()
        
        return {
            "status": "success",
            "cache_statistics": stats,
            "recommendation": _get_cache_recommendation(stats)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadisticas de cache: {str(e)}"
        )

@router.post("/cleanup-cache")
async def cleanup_expired_cache():
    """
    Limpia entradas expiradas del cache
    """
    try:
        cleaned_count = cache_service.cleanup_expired()
        
        return {
            "status": "success",
            "cleaned_entries": cleaned_count,
            "message": f"Se limpiaron {cleaned_count} entradas expiradas del cache"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error limpiando cache: {str(e)}"
        )

@router.post("/analyze-complexity")
async def analyze_query_complexity(message: str):
    """
    Analiza la complejidad de una consulta para ver que presupuesto recibiria
    """
    try:
        complexity_level, complexity_factor = budget_service.analyze_query_complexity(message)
        
        # Calcular presupuesto
        budget = budget_service.calculate_adaptive_budget(
            message,
            history_length=0,
            available_context=settings.MAX_CONTEXT_LENGTH,
            require_analysis=False
        )
        
        return {
            "status": "success",
            "query": message,
            "complexity_analysis": {
                "level": complexity_level,
                "factor": complexity_factor,
                "budget": budget,
                "quality_estimate": budget_service.estimate_response_quality(
                    complexity_level,
                    budget['total_allocated']
                )
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analizando complejidad: {str(e)}"
        )

def _get_cache_recommendation(stats: Dict) -> str:
    """
    Genera recomendacion basada en estadisticas de cache
    """
    hit_rate = stats.get('hit_rate_percent', 0)
    
    if hit_rate >= 70:
        return "Excelente desempeno del cache"
    elif hit_rate >= 50:
        return "Desempeno moderado del cache - considere revisar patrones de consulta"
    elif hit_rate >= 30:
        return "Desempeno bajo del cache - muchas consultas unicas"
    else:
        return "Cache subutilizado - las consultas son muy variadas"
