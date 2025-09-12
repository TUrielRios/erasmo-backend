"""
Configuración central de la aplicación usando Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Configuración del servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False  # Por defecto False por seguridad
    
    # Configuración de CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000", 
        "http://localhost:8080",
        "http://localhost:5173"
    ]
    
    # Configuración de autenticación JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fallback-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 días
    
    # Configuración de OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Configuración de Vector Database
    VECTOR_DB_TYPE: str = "pinecone"
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "")
    PINECONE_INDEX_NAME: str = "erasmo-knowledge"
    
    # Configuración de PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/erasmo")
    DATABASE_HOST: str = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))
    DATABASE_USER: str = os.getenv("DATABASE_USER", "postgres")
    DATABASE_PASSWORD: str = os.getenv("DATABASE_PASSWORD", "admin")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "erasmo")
    
    # Configuración de embeddings
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_DIMENSION: int = 1536
    
    # Configuración de archivos
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".txt", ".md"]
    
    # Configuración de conversación
    MAX_CONTEXT_LENGTH: int = 4000
    CONVERSATION_MEMORY_SIZE: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignorar variables extra no definidas

# Instancia global de configuración
settings = Settings()

# Validación de configuraciones requeridas
def validate_settings():
    if not settings.OPENAI_API_KEY:
        print("⚠️  ADVERTENCIA: OPENAI_API_KEY no está configurada")
    if not settings.PINECONE_API_KEY:
        print("⚠️  ADVERTENCIA: PINECONE_API_KEY no está configurada")
    if settings.DEBUG:
        print("⚠️  MODO DEBUG ACTIVADO - No usar en producción")

validate_settings()