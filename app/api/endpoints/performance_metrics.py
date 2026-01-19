"""
Endpoint para monitoreo de rendimiento y optimizacion de tokens
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.token_performance_monitor import TokenPerformanceMonitor
from typing import Optional

router = APIRouter(prefix="/api/v1/performance", tags=["performance"])

# Instancia global del monitor
monitor = TokenPerformanceMonitor()

@router.get("/system-health")
async def get_system_health():
    """
    Obtiene salud del sistema y estadisticas globales de tokens
    """
    stats = monitor.get_global_stats()
    return {
        "status": "success",
        "data": stats,
        "message": f"Sistema en estado {stats['system_health']}"
    }

@router.get("/session/{session_id}")
async def get_session_metrics(session_id: str):
    """
    Obtiene metricas detalladas de una sesion especifica
    """
    summary = monitor.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "status": "success",
        "data": summary
    }

@router.get("/recommendations/{session_id}")
async def get_optimization_recommendations(session_id: str):
    """
    Obtiene recomendaciones de optimizacion para una sesion
    """
    summary = monitor.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "status": "success",
        "data": {
            "efficiency_score": summary['efficiency_score'],
            "recommendations": summary['recommendations'],
            "metrics": {
                "cache_hit_rate": summary['cache_hit_rate'],
                "avg_latency_ms": summary['avg_latency_ms'],
                "tokens_used": summary['total_tokens'],
                "estimated_cost": summary['estimated_cost']
            }
        }
    }

@router.post("/session/{session_id}/record")
async def record_message_metrics(
    session_id: str,
    role: str = Query(..., description="user o assistant"),
    tokens: int = Query(..., description="Numero de tokens"),
    latency: float = Query(..., description="Latencia en segundos"),
    cached: bool = Query(False, description="Fue cacheado?")
):
    """
    Registra metricas de un mensaje en una sesion
    """
    try:
        monitor.record_message(session_id, role, tokens, latency, cached)
        return {
            "status": "success",
            "message": "Metricas registradas correctamente"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_system_statistics():
    """
    Obtiene estadisticas completas del sistema
    """
    return {
        "status": "success",
        "data": monitor.get_global_stats()
    }
