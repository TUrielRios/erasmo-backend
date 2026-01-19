#!/usr/bin/env python3
"""
Script para crear las nuevas tablas del sistema multi-tenant
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Agregar el directorio raiz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def create_multi_tenant_tables():
    """Crea las nuevas tablas para el sistema multi-tenant"""
    
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
        
        print(" Creando tablas para sistema multi-tenant...")
        
        # Crear tabla companies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                industry VARCHAR(255) NOT NULL,
                sector VARCHAR(255) NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """)
        print("[OK] Tabla 'companies' creada")
        
        # Crear tabla ai_configurations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_configurations (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                methodology_prompt TEXT,
                knowledge_base JSONB,
                personality_traits JSONB,
                response_style VARCHAR(100) DEFAULT 'professional',
                model_name VARCHAR(100) DEFAULT 'gpt-4',
                temperature VARCHAR(10) DEFAULT '0.7',
                max_tokens INTEGER DEFAULT 2000,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """)
        print("[OK] Tabla 'ai_configurations' creada")
        
        # Agregar nuevas columnas a la tabla users
        print("[REFRESH] Actualizando tabla 'users'...")
        
        # Verificar si las columnas ya existen
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name IN ('company_id', 'work_area', 'role')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        if 'company_id' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN company_id INTEGER REFERENCES companies(id)")
            print("[OK] Columna 'company_id' agregada a users")
        
        if 'work_area' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN work_area VARCHAR(255)")
            print("[OK] Columna 'work_area' agregada a users")
        
        if 'role' not in existing_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'client'")
            print("[OK] Columna 'role' agregada a users")
        
        # Crear indices para optimizar consultas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_configurations_company_id ON ai_configurations(company_id)")
        print("[OK] Indices creados")
        
        # Crear companias de ejemplo y configurar usuario admin
        print(" Creando datos iniciales...")
        
        # Crear compania por defecto para admin
        cursor.execute("""
            INSERT INTO companies (name, industry, sector, description)
            VALUES ('Erasmo AI', 'Tecnologia', 'Inteligencia Artificial', 'Plataforma de IA conversacional')
            ON CONFLICT (name) DO NOTHING
        """)
        
        # Obtener ID de la compania Erasmo AI
        cursor.execute("SELECT id FROM companies WHERE name = 'Erasmo AI'")
        erasmo_company_id = cursor.fetchone()[0]
        
        # Actualizar usuario admin
        cursor.execute("""
            UPDATE users 
            SET company_id = %s, work_area = 'Administracion', role = 'admin'
            WHERE username = 'admin'
        """, (erasmo_company_id,))
        print("[OK] Usuario admin actualizado")
        
        # Crear configuracion de IA por defecto para Erasmo AI
        cursor.execute("""
            INSERT INTO ai_configurations (
                company_id, 
                methodology_prompt, 
                personality_traits,
                response_style
            )
            VALUES (
                %s,
                'Eres un asistente de IA especializado en consultoria estrategica. Proporciona respuestas estructuradas, profesionales y orientadas a la accion.',
                '{"expertise": "strategic_consulting", "tone": "professional", "approach": "analytical"}',
                'professional'
            )
            ON CONFLICT DO NOTHING
        """, (erasmo_company_id,))
        print("[OK] Configuracion de IA por defecto creada")
        
        print(" Sistema multi-tenant configurado exitosamente!")
        print("[IDEA] Ahora las companias pueden tener configuraciones de IA personalizadas")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERR] Error creando tablas multi-tenant: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("[LAUNCH] Iniciando creacion de sistema multi-tenant...")
    success = create_multi_tenant_tables()
    if success:
        print(" Sistema multi-tenant creado exitosamente!")
    else:
        print("[ERR] Error en la creacion del sistema multi-tenant")
        sys.exit(1)
