"""
Script para inicializar la base de datos PostgreSQL
Crea las tablas necesarias para el sistema de memoria conversacional
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import engine, Base
from app.models.conversation import Conversation, Message
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Inicializa la base de datos creando todas las tablas"""
    
    try:
        logger.info("🔧 Inicializando base de datos PostgreSQL...")
        logger.info(f"📍 Conectando a: {settings.DATABASE_URL}")
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Tablas creadas exitosamente:")
        logger.info("   - conversations (conversaciones)")
        logger.info("   - messages (mensajes)")
        
        # Verificar conexión
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✅ Conexión a PostgreSQL verificada")
        
        logger.info("🎉 Base de datos inicializada correctamente")
        
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        logger.error("💡 Asegúrate de que PostgreSQL esté ejecutándose:")
        logger.error("   docker-compose up postgres")
        raise

if __name__ == "__main__":
    init_database()
