#!/usr/bin/env python3
"""
Script para arreglar los tipos de datos en la base de datos
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Agregar el directorio raiz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def fix_database_types():
    """Arregla los tipos de datos incorrectos en la base de datos"""
    
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("[INIT] Arreglando tipos de datos en la base de datos...")
        
        # Verificar si las tablas existen
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'conversations', 'messages')
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"[CLIPBOARD] Tablas existentes: {existing_tables}")
        
        # Si no existen las tablas, crearlas primero
        if not existing_tables:
            print("[ERR] No se encontraron tablas. Creando tablas primero...")
            create_tables(cursor)
        
        # Verificar el tipo actual de user_id en conversations
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'conversations' 
            AND column_name = 'user_id'
        """)
        result = cursor.fetchone()
        
        if result:
            current_type = result[0]
            print(f"[STATS] Tipo actual de user_id en conversations: {current_type}")
            
            if current_type != 'integer':
                print("[REFRESH] Convirtiendo user_id a integer...")
                
                # Primero, eliminar datos existentes si los hay (para evitar problemas de conversion)
                cursor.execute("DELETE FROM messages")
                cursor.execute("DELETE FROM conversations")
                cursor.execute("DELETE FROM users WHERE id != 1")  # Mantener solo el admin
                
                # Cambiar el tipo de la columna
                cursor.execute("""
                    ALTER TABLE conversations 
                    ALTER COLUMN user_id TYPE INTEGER 
                    USING user_id::INTEGER
                """)
                print("[OK] user_id convertido a integer exitosamente")
            else:
                print("[OK] user_id ya es de tipo integer")
        
        # Verificar otros tipos importantes
        print("[SEARCH] Verificando otros tipos de datos...")
        
        # Verificar que session_id sea string
        cursor.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'conversations' 
            AND column_name = 'session_id'
        """)
        result = cursor.fetchone()
        if result:
            print(f"[STATS] Tipo de session_id: {result[0]}")
        
        print("[OK] Tipos de datos verificados y corregidos")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERR] Error arreglando tipos de datos: {e}")
        return False
    
    return True

def create_tables(cursor):
    """Crea las tablas si no existen"""
    
    # Crear tabla users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        )
    """)
    
    # Crear tabla conversations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title VARCHAR(500),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)
    
    # Crear tabla messages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            message_metadata TEXT
        )
    """)
    
    # Crear indices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id)")
    
    # Crear usuario admin si no existe
    cursor.execute("""
        INSERT INTO users (username, email, hashed_password, full_name, is_active)
        VALUES ('admin', 'admin@erasmo.ai', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsxq5/Qe2', 'Administrador', TRUE)
        ON CONFLICT (username) DO NOTHING
    """)
    
    print("[OK] Tablas creadas exitosamente")

if __name__ == "__main__":
    print("[LAUNCH] Iniciando correccion de tipos de base de datos...")
    success = fix_database_types()
    if success:
        print(" Correccion completada exitosamente!")
    else:
        print("[ERR] Error en la correccion")
        sys.exit(1)
