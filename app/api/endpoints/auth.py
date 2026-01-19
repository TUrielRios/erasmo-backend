"""
Endpoints de autenticacion simplificados - sin JWT
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.auth_service import AuthService
from app.models.schemas import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registrar nuevo usuario con compania"""
    try:
        user = AuthService.create_user(db, user_data)
        return UserResponse.from_orm(user)
        
    except ValueError as e:
        # Errores de validacion del servicio
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear usuario: {str(e)}"
        )

@router.post("/login")
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Iniciar sesion - solo verificacion de contrasena"""
    # Autenticar usuario
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    
    return {
        "message": "Login exitoso",
        "user": UserResponse.from_orm(user)
    }

@router.post("/logout")
async def logout():
    """Cerrar sesion"""
    return {"message": "Sesion cerrada correctamente"}
