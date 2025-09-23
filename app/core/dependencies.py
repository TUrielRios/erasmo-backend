"""
Dependencias simplificadas - sin JWT
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db

# Ahora solo proporcionamos acceso a la base de datos
# La autenticación se maneja directamente en cada endpoint si es necesario

def get_database() -> Session:
    """Obtener sesión de base de datos"""
    return Depends(get_db)
