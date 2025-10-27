"""
Endpoints para gestión de usuarios
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.user import User
from app.models.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/company/{company_id}", response_model=List[UserResponse])
async def get_company_users(
    company_id: int,
    user_id: int = Query(..., description="ID del usuario que hace la petición"),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los usuarios de una compañía.
    Solo usuarios de la misma compañía pueden ver esta información.
    """
    # Verificar que el usuario que hace la petición existe y pertenece a la compañía
    requesting_user = db.query(User).filter(User.id == user_id).first()
    
    if not requesting_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    if requesting_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver los usuarios de esta compañía"
        )
    
    # Obtener todos los usuarios activos de la compañía
    users = db.query(User).filter(
        User.company_id == company_id,
        User.is_active == True
    ).all()
    
    return [UserResponse.from_orm(user) for user in users]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    requesting_user_id: int = Query(..., description="ID del usuario que hace la petición"),
    db: Session = Depends(get_db)
):
    """
    Obtener información de un usuario específico.
    Solo usuarios de la misma compañía pueden ver esta información.
    """
    # Verificar que el usuario que hace la petición existe
    requesting_user = db.query(User).filter(User.id == requesting_user_id).first()
    
    if not requesting_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario solicitante no encontrado"
        )
    
    # Obtener el usuario solicitado
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar que ambos usuarios pertenecen a la misma compañía
    if requesting_user.company_id != user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver este usuario"
        )
    
    return UserResponse.from_orm(user)
