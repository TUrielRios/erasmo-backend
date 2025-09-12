"""
Endpoints de autenticación
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.auth_service import AuthService
from app.models.schemas import UserCreate, UserLogin, UserResponse, AuthResponse
from app.core.dependencies import get_current_active_user
from app.models.conversation import User

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=AuthResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registrar nuevo usuario"""
    try:
        # Crear usuario
        user = AuthService.create_user(db, user_data)
        
        # Crear tokens JWT
        access_token = AuthService.create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        refresh_token = AuthService.create_refresh_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        return AuthResponse(
            user=UserResponse.from_orm(user),
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear usuario: {str(e)}"
        )

@router.post("/login", response_model=AuthResponse)
async def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Iniciar sesión"""
    # Autenticar usuario
    user = AuthService.authenticate_user(db, login_data.email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )
    
    # Crear tokens JWT
    access_token = AuthService.create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    refresh_token = AuthService.create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    return AuthResponse(
        user=UserResponse.from_orm(user),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Obtener información del usuario actual"""
    return UserResponse.from_orm(current_user)

@router.post("/logout")
async def logout():
    """Cerrar sesión"""
    return {"message": "Sesión cerrada correctamente"}

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Renovar token de acceso usando refresh token"""
    token_data = AuthService.verify_token(refresh_token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh inválido"
        )
    
    user = AuthService.get_user_by_id(db, token_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    # Crear nuevos tokens
    access_token = AuthService.create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    new_refresh_token = AuthService.create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    return AuthResponse(
        user=UserResponse.from_orm(user),
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )
