"""
Configuración de base de datos PostgreSQL para memoria conversacional
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Crear engine de SQLAlchemy
engine = create_engine(settings.DATABASE_URL)

# Crear SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

def get_db():
    """Dependency para obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Inicializar base de datos y crear tablas"""
    try:
        from app.models.user import User
        from app.models.company import Company
        from app.models.conversation import Conversation, Message
        from app.models.project import Project, ProjectShare, ConversationShare
        from app.models.project_file import ProjectFile
        
        Base.metadata.create_all(bind=engine)
        print("✅ Base de datos PostgreSQL inicializada correctamente")
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        raise
