"""
Configuracion central de la aplicacion
Compatible con .env sin parseos JSON raros
"""

import os
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class Settings:
    # =========================
    # Servidor
    # =========================
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # =========================
    # Seguridad / Sesiones
    # =========================
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "dev-secret-key-change-in-production"
    )

    # =========================
    # CORS
    # =========================
    @property
    def ALLOWED_ORIGINS(self) -> list[str]:
        raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        try:
            # Intentar parsear como lista JSON
            if raw_origins.startswith("[") and raw_origins.endswith("]"):
                return json.loads(raw_origins)
            # Fallback a split por coma
            return [o.strip() for o in raw_origins.split(",") if o.strip()]
        except Exception:
            return ["http://localhost:3000"]

    # Mantener como atributo de clase para compatibilidad si es necesario, 
    # pero mejor usar una propiedad o cargarlo en __init__
    def __init__(self):
        # Cargar otros valores normales
        pass

    # =========================
    # OpenAI
    # =========================
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # =========================
    # Vector DB (Pinecone)
    # =========================
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "pinecone")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv(
        "PINECONE_INDEX_NAME",
        "erasmo-knowledge"
    )

    # =========================
    # Base de datos
    # =========================
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # =========================
    # Embeddings
    # =========================
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "text-embedding-ada-002"
    )
    EMBEDDING_DIMENSION: int = int(
        os.getenv("EMBEDDING_DIMENSION", "1536")
    )

    # =========================
    # Archivos
    # =========================
    MAX_FILE_SIZE: int = int(
        os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024))
    )

    ALLOWED_FILE_TYPES: list[str] = os.getenv(
        "ALLOWED_FILE_TYPES",
        ".txt,.md"
    ).split(",")

    # =========================
    # Conversacion
    # =========================
    MAX_CONTEXT_LENGTH: int = int(
        os.getenv("MAX_CONTEXT_LENGTH", "8000")
    )
    CONVERSATION_MEMORY_SIZE: int = int(
        os.getenv("CONVERSATION_MEMORY_SIZE", "10")
    )
    
    # =========================
    # OpenAI Response Settings
    # =========================
    DEFAULT_TEMPERATURE: float = float(
        os.getenv("DEFAULT_TEMPERATURE", "0.7")
    )
    DEFAULT_TOP_P: float = float(
        os.getenv("DEFAULT_TOP_P", "0.9")
    )
    MAX_RESPONSE_TOKENS: int = int(
        os.getenv("MAX_RESPONSE_TOKENS", "4000")
    )
    TOKEN_BUDGET_BUFFER: int = int(
        os.getenv("TOKEN_BUDGET_BUFFER", "1000")
    )


# Instancia global
settings = Settings()


# Logs de validacion (no rompe)
def validate_settings():
    print("[OK] Config cargada correctamente")
    print(f"   -> DEBUG: {settings.DEBUG}")
    print(f"   -> HOST: {settings.HOST}:{settings.PORT}")
    print(f"   -> CORS: {settings.ALLOWED_ORIGINS}")

    if not settings.OPENAI_API_KEY:
        print("[WARN] OPENAI_API_KEY no configurada")
    if not settings.PINECONE_API_KEY:
        print("[WARN] PINECONE_API_KEY no configurada")
    if not settings.DATABASE_URL:
        print("[WARN] DATABASE_URL no configurada")


validate_settings()
