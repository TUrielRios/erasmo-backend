#!/usr/bin/env python3
"""
Script para migrar datos existentes al nuevo sistema multi-tenant
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def migrate_existing_data():
    """Migra datos existentes al nuevo esquema multi-tenant"""
    
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
        
        print("🔄 Migrando datos existentes al sistema multi-tenant...")
        
        # Verificar usuarios sin compañía asignada
        cursor.execute("""
            SELECT id, username, email, full_name 
            FROM users 
            WHERE company_id IS NULL AND username != 'admin'
        """)
        users_without_company = cursor.fetchall()
        
        if users_without_company:
            print(f"👥 Encontrados {len(users_without_company)} usuarios sin compañía asignada")
            
            # Crear compañía "Sin Asignar" para usuarios existentes
            cursor.execute("""
                INSERT INTO companies (name, industry, sector, description)
                VALUES ('Sin Asignar', 'General', 'General', 'Compañía temporal para usuarios existentes')
                ON CONFLICT (name) DO NOTHING
            """)
            
            # Obtener ID de la compañía "Sin Asignar"
            cursor.execute("SELECT id FROM companies WHERE name = 'Sin Asignar'")
            unassigned_company_id = cursor.fetchone()[0]
            
            # Asignar usuarios a la compañía "Sin Asignar"
            cursor.execute("""
                UPDATE users 
                SET company_id = %s, work_area = 'General', role = 'client'
                WHERE company_id IS NULL AND username != 'admin'
            """, (unassigned_company_id,))
            
            print(f"✅ {len(users_without_company)} usuarios asignados a compañía temporal")
            
            # Crear configuración de IA por defecto para la compañía "Sin Asignar"
            cursor.execute("""
                INSERT INTO ai_configurations (
                    company_id, 
                    methodology_prompt, 
                    personality_traits,
                    response_style
                )
                VALUES (
                    %s,
                    'Eres un asistente de IA general. Proporciona respuestas útiles y profesionales.',
                    '{"expertise": "general", "tone": "friendly", "approach": "helpful"}',
                    'professional'
                )
                ON CONFLICT DO NOTHING
            """, (unassigned_company_id,))
            
            print("✅ Configuración de IA creada para usuarios sin asignar")
        
        # Verificar integridad de datos
        cursor.execute("SELECT COUNT(*) FROM users WHERE company_id IS NULL")
        users_without_company_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM companies")
        companies_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ai_configurations")
        ai_configs_count = cursor.fetchone()[0]
        
        print(f"📊 Estado final:")
        print(f"   - Usuarios sin compañía: {users_without_company_count}")
        print(f"   - Total de compañías: {companies_count}")
        print(f"   - Configuraciones de IA: {ai_configs_count}")
        
        if users_without_company_count == 0:
            print("✅ Todos los usuarios tienen compañía asignada")
        else:
            print("⚠️  Algunos usuarios aún no tienen compañía asignada")
        
        print("🎉 Migración de datos completada!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error migrando datos: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando migración de datos existentes...")
    success = migrate_existing_data()
    if success:
        print("🎉 Migración completada exitosamente!")
    else:
        print("❌ Error en la migración")
        sys.exit(1)
