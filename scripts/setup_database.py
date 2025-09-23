"""
Script completo para configurar la base de datos desde cero
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.database import Base
from app.models.user import User
from app.models.conversation import Conversation, Message
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_database():
    """Configurar la base de datos completamente desde cero"""
    
    try:
        logger.info("🔧 Configurando base de datos PostgreSQL...")
        logger.info(f"📍 Conectando a: {settings.DATABASE_URL}")
        
        # Crear engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Tablas creadas exitosamente:")
        logger.info("   - users (usuarios)")
        logger.info("   - conversations (conversaciones)")
        logger.info("   - messages (mensajes)")
        
        # Crear usuario administrador por defecto
        with engine.connect() as conn:
            # Verificar si ya existe el usuario admin
            result = conn.execute(text("SELECT id FROM users WHERE username = 'admin'"))
            admin_user = result.fetchone()
            
            if not admin_user:
                logger.info("👤 Creando usuario administrador por defecto...")
                conn.execute(text("""INSERT INTO users (username, email, hashed_password, full_name, is_active) VALUES ('admin', 'admin@erasmo.ai', '$2b$12$dummy_hash', 'Administrador', true)"""))
                conn.commit()
                logger.info("✅ Usuario administrador creado")
            else:
                logger.info("👤 Usuario administrador ya existe")
        
        # Verificar conexión
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✅ Conexión a PostgreSQL verificada")
        
        logger.info("🎉 Base de datos configurada correctamente")
        logger.info("💡 Ahora puedes ejecutar el servidor: python main.py")
        
    except Exception as e:
        logger.error(f"❌ Error configurando base de datos: {e}")
        logger.error("💡 Asegúrate de que PostgreSQL esté ejecutándose:")
        logger.error("   docker-compose up postgres")
        raise

if __name__ == "__main__":
    setup_database()
