"""
Erasmo Estratégico Verbal - Fase 1
Backend principal para agente conversacional estratégico

Este archivo inicializa el servidor FastAPI y configura todos los endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
from dotenv import load_dotenv

from app.api.endpoints.health import router as health_router
from app.api.endpoints.ingest import router as ingest_router
from app.api.endpoints.query import router as query_router
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.chat import router as chat_router
from app.api.endpoints.admin import router as admin_router  # Agregado router de administración
from app.api.endpoints.projects import router as projects_router  # Added projects router
from app.api.endpoints.project_files import router as project_files_router  # Added project files router
from app.api.endpoints.users import router as users_router  # Added users router
from app.core.config import settings
from app.db.vector_store import VectorStore
from app.db.database import init_db

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup: Inicializar conexiones a bases de datos
    logger.info("Inicializando Erasmo Backend...")
    
    try:
        await init_db()
        logger.info("✅ Base de datos PostgreSQL inicializada")
    except Exception as e:
        logger.error(f"❌ Error inicializando PostgreSQL: {e}")
        # Continue without memory if DB fails
        logger.warning("⚠️ Continuando sin memoria persistente")
    
    # Inicializar vector store
    vector_store = VectorStore()
    await vector_store.initialize()
    app.state.vector_store = vector_store
    
    logger.info("✅ Erasmo Backend inicializado correctamente")
    
    yield
    
    # Shutdown: Limpiar recursos
    logger.info("Cerrando conexiones...")
    await vector_store.close()

# Crear aplicación FastAPI
app = FastAPI(
    title="Erasmo Estratégico Verbal - Backend",
    description="Backend para agente conversacional estratégico con capacidades de ingesta de conocimiento y respuestas estructuradas",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(ingest_router, prefix="/api/v1", tags=["ingestion"])
app.include_router(query_router, prefix="/api/v1", tags=["conversation"])
app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])
app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
app.include_router(admin_router, prefix="/api/v1", tags=["administration"])  # Incluido router de administración
app.include_router(projects_router, prefix="/api/v1", tags=["projects"])  # Included projects router
app.include_router(project_files_router, prefix="/api/v1", tags=["project_files"])  # Included project files router
app.include_router(users_router, prefix="/api/v1", tags=["users"])  # Included users router

@app.get("/")
async def root():
    """Endpoint raíz con información básica"""
    return {
        "message": "Erasmo Estratégico Verbal - Backend API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
