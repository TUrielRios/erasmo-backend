"""
Dependencias simplificadas - sin JWT
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db

# Ahora solo proporcionamos acceso a la base de datos
# La autenticacion se maneja directamente en cada endpoint si es necesario

def get_database() -> Session:
    """Obtener sesion de base de datos"""
    return Depends(get_db)
