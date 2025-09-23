"""
Servicio de autenticación simplificado - solo verificación de contraseñas
"""

from typing import Optional
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.company import Company
from app.models.schemas import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Servicio para manejo de autenticación simplificado"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generar hash de contraseña"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Crear nuevo usuario con compañía"""
        try:
            company = db.query(Company).filter(
                Company.name == user_data.company_name
            ).first()
            
            if not company:
                # Crear nueva compañía
                company = Company(
                    name=user_data.company_name,
                    industry=user_data.industry,
                    sector=user_data.sector,
                    description=f"Compañía en el sector {user_data.sector} de la industria {user_data.industry}",
                    is_active=True
                )
                db.add(company)
                db.flush()  # Para obtener el ID de la compañía
            
            # Verificar si el usuario ya existe
            existing_user = db.query(User).filter(
                (User.email == user_data.email) | (User.username == user_data.username)
            ).first()
            
            if existing_user:
                if existing_user.email == user_data.email:
                    raise ValueError("El email ya está registrado")
                else:
                    raise ValueError("El nombre de usuario ya está en uso")
            
            hashed_password = AuthService.get_password_hash(user_data.password)
            
            db_user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                work_area=user_data.work_area,
                company_id=company.id,
                role="client",  # Por defecto todos los usuarios son clientes
                is_active=True
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Cargar la relación con la compañía
            db.refresh(db_user)
            
            return db_user
            
        except IntegrityError as e:
            db.rollback()
            if "users_email_key" in str(e):
                raise ValueError("El email ya está registrado")
            elif "users_username_key" in str(e):
                raise ValueError("El nombre de usuario ya está en uso")
            else:
                raise ValueError(f"Error de integridad en la base de datos: {str(e)}")
        except Exception as e:
            db.rollback()
            raise ValueError(f"Error al crear usuario: {str(e)}")
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Autenticar usuario por email y contraseña"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Obtener usuario por nombre de usuario"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Obtener usuario por ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_with_company(db: Session, user_id: int) -> Optional[User]:
        """Obtener usuario con información de compañía cargada"""
        from sqlalchemy.orm import joinedload
        return db.query(User).options(joinedload(User.company)).filter(User.id == user_id).first()
    
    @staticmethod
    def is_admin(user: User) -> bool:
        """Verificar si el usuario es administrador"""
        return user.role == "admin" and user.is_active
    
    @staticmethod
    def is_client(user: User) -> bool:
        """Verificar si el usuario es cliente"""
        return user.role == "client" and user.is_active
