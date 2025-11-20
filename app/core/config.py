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
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 días para refresh tokens
    
    # Configuración de OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o-mini"  # gpt-4o-mini supports up to 16K output tokens
    OPENAI_MODEL_MINI: str = "gpt-4o-mini"  # Fallback for quick analyses
    OPENAI_MODEL_ADVANCED: str = "gpt-4o"  # Advanced model for complex tasks (16K output tokens)
    
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
    ALLOWED_FILE_TYPES: List[str] = [
        ".txt", ".md",           # Text files
        ".pdf",                  # PDF documents
        ".docx", ".doc",         # Word documents
        ".xlsx", ".xls",         # Excel spreadsheets
        ".pptx", ".ppt",         # PowerPoint presentations
        ".png", ".jpg", ".jpeg"  # Images/Screenshots
    ]
    
    # Configuración de conversación
    MAX_CONTEXT_LENGTH: int = 128000  # Maximum context tokens the model can process
    CONVERSATION_MEMORY_SIZE: int = 300  # Number of messages to keep in memory
    
    # Nuevas configuraciones para optimización de tokens
    MAX_RESPONSE_TOKENS: int = 15000  # Safe limit under 16,384 max
    MIN_RESPONSE_TOKENS: int = 1000   # Minimum for detailed responses
    TOKEN_BUDGET_BUFFER: int = 2000   # Safety buffer for token calculations
    
    ENABLE_ADVANCED_CACHING: bool = True
    ENABLE_STREAMING_OPTIMIZATION: bool = True
    ENABLE_RAAG: bool = True  # Retrieval Augmented Analysis Generation
    MAX_PARALLEL_SEARCHES: int = 10  # Aumentado de 5 a 10
    CACHE_TTL_SECONDS: int = 7200  # Aumentado de 3600 a 7200 (2 horas)
    ENABLE_RESPONSE_REFINEMENT: bool = True  # Refinar respuestas con análisis secundario
    ENABLE_CONTEXT_RERANKING: bool = True  # Re-rankear contexto por relevancia
    
    ENABLE_TOKEN_OPTIMIZATION: bool = True
    ENABLE_CONTEXT_CACHING: bool = True
    MAX_SEARCH_RESULTS: int = 100  # Aumentado de 50 a 100 (2x)
    
    # Nuevas configuraciones para temperatura y creatividad
    DEFAULT_TEMPERATURE: float = 0.95  # Increased for more verbose responses
    DEFAULT_TOP_P: float = 0.98  # Increased for maximum diversity
    
    # Nuevas configuraciones para presupuesto de tokens adaptable
    ENABLE_ADAPTIVE_TOKEN_BUDGET: bool = True
    MAX_ADAPTIVE_MULTIPLIER: float = 2.5  # Respuestas complejas pueden usar 2.5x más tokens
    
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
    print(f"✅ Configuración cargada: Modelo={settings.OPENAI_MODEL}, MaxContextTokens={settings.MAX_CONTEXT_LENGTH}")

validate_settings()
