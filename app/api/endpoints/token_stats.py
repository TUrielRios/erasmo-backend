from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db.database import get_db
from app.services.token_logger_service import TokenLoggerService

router = APIRouter(prefix="/api/v1/tokens", tags=["tokens"])

# Global token logger instance
token_logger = TokenLoggerService()

@router.get("/session/{session_id}")
def get_session_token_stats(
    session_id: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtiene estadísticas de tokens usado en una sesión
    """
    return token_logger.get_session_stats(session_id)

@router.get("/health")
def token_stats_health() -> Dict[str, str]:
    """
    Verifica que el servicio de estadísticas de tokens está activo
    """
    return {
        "status": "active",
        "message": "Token statistics service is running",
        "total_logs": len(token_logger.logs)
    }
