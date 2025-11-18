"""
Endpoints para monitoreo y optimización de tokens y rendimiento de la IA
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.db.database import get_db
from app.services.auth_service import AuthService
from app.services.token_optimizer_service import TokenOptimizerService
from app.services.smart_cache_service import SmartCacheService
from app.core.config import settings

router = APIRouter(prefix="/optimization", tags=["optimization"])
token_optimizer = TokenOptimizerService()
smart_cache = SmartCacheService()

@router.get("/token-budget")
async def get_token_budget(user_id: int = Query(...)) -> Dict[str, Any]:
    """
    Obtiene información del presupuesto de tokens disponible
    """
    try:
        total_budget = token_optimizer.calculate_total_budget()
        
        allocations = {
            "full_analysis": token_optimizer.allocate_budget("full_analysis"),
            "normal_chat": token_optimizer.allocate_budget("normal_chat"),
            "quick_response": token_optimizer.allocate_budget("quick_response")
        }
        
        return {
            "model": settings.OPENAI_MODEL,
            "total_budget_tokens": total_budget,
            "max_context_length": settings.MAX_CONTEXT_LENGTH,
            "max_response_tokens": settings.MAX_RESPONSE_TOKENS,
            "token_optimization_enabled": settings.ENABLE_TOKEN_OPTIMIZATION,
            "context_caching_enabled": settings.ENABLE_CONTEXT_CACHING,
            "allocations": allocations,
            "buffer_tokens": settings.TOKEN_BUDGET_BUFFER
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo presupuesto de tokens: {str(e)}"
        )

@router.get("/session-stats/{session_id}")
async def get_session_stats(
    session_id: str,
    user_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtiene estadísticas de uso de tokens para una sesión específica
    """
    try:
        # Verificar que el usuario existe
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        stats = token_optimizer.get_token_stats(session_id)
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "stats": stats,
            "optimization_enabled": settings.ENABLE_TOKEN_OPTIMIZATION
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )

@router.get("/performance-recommendations")
async def get_performance_recommendations(
    user_id: int = Query(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtiene recomendaciones para mejorar el rendimiento basadas en configuración
    """
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        recommendations = {
            "current_config": {
                "max_context_length": settings.MAX_CONTEXT_LENGTH,
                "conversation_memory_size": settings.CONVERSATION_MEMORY_SIZE,
                "max_response_tokens": settings.MAX_RESPONSE_TOKENS,
                "enable_token_optimization": settings.ENABLE_TOKEN_OPTIMIZATION,
                "enable_context_caching": settings.ENABLE_CONTEXT_CACHING,
                "max_search_results": settings.MAX_SEARCH_RESULTS
            },
            "recommendations": [
                {
                    "category": "tokens",
                    "current": settings.MAX_RESPONSE_TOKENS,
                    "recommended": 8000,
                    "benefit": "Respuestas más detalladas y exhaustivas",
                    "status": "optimized" if settings.MAX_RESPONSE_TOKENS >= 8000 else "can_improve"
                },
                {
                    "category": "context_length",
                    "current": settings.MAX_CONTEXT_LENGTH,
                    "recommended": 16000,
                    "benefit": "Mejor comprensión de conversaciones largas",
                    "status": "optimized" if settings.MAX_CONTEXT_LENGTH >= 16000 else "can_improve"
                },
                {
                    "category": "memory_size",
                    "current": settings.CONVERSATION_MEMORY_SIZE,
                    "recommended": 50,
                    "benefit": "Mejor retención de información histórica",
                    "status": "optimized" if settings.CONVERSATION_MEMORY_SIZE >= 50 else "can_improve"
                },
                {
                    "category": "search_results",
                    "current": settings.MAX_SEARCH_RESULTS,
                    "recommended": 25,
                    "benefit": "Contexto más relevante y diverso",
                    "status": "optimized" if settings.MAX_SEARCH_RESULTS >= 25 else "can_improve"
                },
                {
                    "category": "optimization",
                    "current": settings.ENABLE_TOKEN_OPTIMIZATION,
                    "recommended": True,
                    "benefit": "Uso eficiente de tokens sin perder calidad",
                    "status": "optimized" if settings.ENABLE_TOKEN_OPTIMIZATION else "can_improve"
                }
            ],
            "global_optimization_status": "fully_optimized" if all([
                settings.MAX_RESPONSE_TOKENS >= 8000,
                settings.MAX_CONTEXT_LENGTH >= 16000,
                settings.CONVERSATION_MEMORY_SIZE >= 50,
                settings.ENABLE_TOKEN_OPTIMIZATION
            ]) else "can_improve"
        }
        
        return recommendations
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo recomendaciones: {str(e)}"
        )

@router.post("/test-optimization")
async def test_optimization(
    user_id: int = Query(...),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Test de optimización para verificar que todo está funcionando correctamente
    """
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(
                status_code=404,
                detail="Usuario no encontrado"
            )
        
        # Crear prompt de prueba
        test_system = "Eres un asistente de prueba. Responde brevemente." * 10
        test_context = [
            {"content": "Información de prueba 1. " * 50, "category": "company_knowledge", "priority": 5, "relevance_score": 0.8},
            {"content": "Información de prueba 2. " * 50, "category": "company_knowledge", "priority": 5, "relevance_score": 0.7},
            {"content": "Información de prueba 3. " * 50, "category": "company_knowledge", "priority": 5, "relevance_score": 0.6},
        ]
        test_history = [
            {"role": "user", "content": "Pregunta de prueba 1"},
            {"role": "assistant", "content": "Respuesta de prueba 1"},
        ] * 5
        
        # Optimizar
        optimized_system, _, optimized_context, optimized_history = token_optimizer.optimize_prompt(
            system_prompt=test_system,
            context=test_context,
            history=test_history,
            user_message="Pregunta de prueba",
            prompt_role="full_analysis"
        )
        
        # Calcular estadísticas
        original_tokens = (
            token_optimizer.count_tokens(test_system) +
            sum(token_optimizer.count_tokens(ctx.get("content", "")) for ctx in test_context) +
            sum(token_optimizer.count_tokens(msg.get("content", "")) for msg in test_history)
        )
        
        optimized_tokens = (
            token_optimizer.count_tokens(optimized_system) +
            sum(token_optimizer.count_tokens(ctx.get("content", "")) for ctx in optimized_context) +
            sum(token_optimizer.count_tokens(msg.get("content", "")) for msg in optimized_history)
        )
        
        savings = original_tokens - optimized_tokens
        savings_percentage = (savings / original_tokens * 100) if original_tokens > 0 else 0
        
        return {
            "test_status": "success",
            "optimization_working": optimized_tokens < original_tokens,
            "metrics": {
                "original_tokens": original_tokens,
                "optimized_tokens": optimized_tokens,
                "tokens_saved": savings,
                "savings_percentage": round(savings_percentage, 2),
                "efficiency_ratio": round(original_tokens / optimized_tokens, 2) if optimized_tokens > 0 else 0
            },
            "features_enabled": {
                "token_optimization": settings.ENABLE_TOKEN_OPTIMIZATION,
                "context_caching": settings.ENABLE_CONTEXT_CACHING
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en test de optimización: {str(e)}"
        )

@router.get("/cache-stats")
async def get_cache_stats(user_id: int = Query(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Obtiene estadísticas del sistema de caché
    """
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        cache_stats = smart_cache.get_cache_stats()
        
        return {
            "cache_enabled": settings.ENABLE_CONTEXT_CACHING,
            "stats": cache_stats,
            "cache_ttl_seconds": smart_cache.ttl_seconds,
            "recommendations": [
                "El caché es más efectivo con conversaciones repetitivas",
                f"Tasa de acierto actual: {cache_stats['hit_rate']}%"
            ] if cache_stats['hit_rate'] > 0 else [
                "El caché mejorará después de varias interacciones"
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo estadísticas de caché: {str(e)}"
        )

@router.post("/cache-cleanup")
async def cleanup_cache(user_id: int = Query(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Limpia elementos expirados del caché
    """
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        deleted_count = smart_cache.cleanup_expired_cache()
        
        return {
            "status": "cleanup_completed",
            "deleted": deleted_count,
            "remaining_cache_items": smart_cache.get_cache_stats()["total_cached_items"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error limpiando caché: {str(e)}"
        )

@router.delete("/cache-reset")
async def reset_cache(user_id: int = Query(...), db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Resetea completamente el caché (use with caution)
    """
    try:
        current_user = AuthService.get_user_by_id(db, user_id)
        if not current_user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Solo admin puede resetear caché global
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Solo administradores pueden resetear el caché"
            )
        
        previous_stats = smart_cache.get_cache_stats()
        smart_cache.response_cache.clear()
        smart_cache.context_cache.clear()
        smart_cache.embedding_cache.clear()
        
        return {
            "status": "cache_reset",
            "previous_stats": previous_stats,
            "message": "Caché completamente limpiado"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reseteando caché: {str(e)}"
        )
