"""
Script para crear las tablas de usuarios en la base de datos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.database import Base
from app.models.user import User
from app.models.conversation import Conversation, Message

def create_user_tables():
    """Crear las tablas de usuarios y actualizar las existentes"""
    
    # Crear engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Crear todas las tablas (incluyendo la nueva tabla users)
        Base.metadata.create_all(bind=engine)
        
        # Actualizar la tabla conversations para agregar la foreign key a users
        with engine.connect() as conn:
            # Verificar si la columna user_id ya es integer
            result = conn.execute(text("""SELECT data_type FROM information_schema.columns WHERE table_name = 'conversations' AND column_name = 'user_id'"""))
            
            current_type = result.fetchone()
            
            if current_type and current_type[0] == 'character varying':
                print("Actualizando columna user_id de String a Integer...")
                
                # Primero, crear un usuario por defecto para conversaciones existentes
                conn.execute(text("""INSERT INTO users (username, email, hashed_password, full_name, is_active) VALUES ('admin', 'admin@example.com', 'temp_hash', 'Usuario Administrador', true) ON CONFLICT (username) DO NOTHING"""))
                
                # Obtener el ID del usuario admin
                admin_user = conn.execute(text("SELECT id FROM users WHERE username = 'admin'")).fetchone()
                admin_id = admin_user[0] if admin_user else 1
                
                # Actualizar conversaciones existentes para usar el admin_id
                conn.execute(text(f"UPDATE conversations SET user_id = '{admin_id}' WHERE user_id IS NULL OR user_id = ''"))
                
                # Cambiar el tipo de columna
                conn.execute(text("ALTER TABLE conversations ALTER COLUMN user_id TYPE INTEGER USING user_id::INTEGER"))
                conn.execute(text("ALTER TABLE conversations ALTER COLUMN user_id SET NOT NULL"))
                
                # Agregar foreign key constraint
                conn.execute(text("""ALTER TABLE conversations ADD CONSTRAINT fk_conversations_user_id FOREIGN KEY (user_id) REFERENCES users(id)"""))
                
            conn.commit()
            print("[OK] Tablas de usuarios creadas y actualizadas exitosamente")
            
    except Exception as e:
        print(f"[ERR] Error al crear tablas: {e}")
        raise

if __name__ == "__main__":
    create_user_tables()
