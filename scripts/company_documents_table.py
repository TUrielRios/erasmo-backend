#!/usr/bin/env python3
"""
Script de migración para crear tabla company_documents
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def create_company_documents_table():
    """
    Crear la tabla company_documents y eliminar ai_configurations
    """
    
    try:
        # Conectar a la base de datos usando la configuración de la app
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🗃️ Iniciando migración de company_documents...")
        
        # Create table for company documents instead of AI configurations
        print("📄 Creando tabla company_documents...")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS company_documents (
            id SERIAL PRIMARY KEY,
            company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
            filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        cursor.execute(create_table_query)
        print("✅ Tabla 'company_documents' creada exitosamente")
        
        # Create indexes for better performance
        print("🔍 Creando índices para mejor rendimiento...")
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_company_documents_company_id ON company_documents(company_id);",
            "CREATE INDEX IF NOT EXISTS idx_company_documents_active ON company_documents(is_active);"
        ]
        
        for index_query in index_queries:
            cursor.execute(index_query)
        
        print("✅ Índices creados exitosamente")
        
        # Drop AI configurations table if it exists (since we're simplifying)
        print("🗑️ Eliminando tabla ai_configurations si existe...")
        drop_table_query = "DROP TABLE IF EXISTS ai_configurations CASCADE;"
        cursor.execute(drop_table_query)
        print("✅ Tabla 'ai_configurations' eliminada exitosamente")
        
        print("\n🎉 Migración completada exitosamente!")
        print("📊 Tabla company_documents lista para usar")
        print("🔗 Relación establecida con tabla companies")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error de base de datos durante la migración: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general durante la migración: {e}")
        return False
    
    return True

def verify_migration():
    """
    Verificar que la migración se ejecutó correctamente
    """
    try:
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        cursor = conn.cursor()
        
        print("\n🔍 Verificando migración...")
        
        # Verificar que la tabla existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'company_documents'
            );
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print("✅ Tabla company_documents existe")
            
            # Verificar índices
            cursor.execute("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename = 'company_documents'
                ORDER BY indexname;
            """)
            
            indexes = cursor.fetchall()
            print(f"✅ Índices encontrados: {len(indexes)}")
            for index in indexes:
                print(f"   - {index[0]}")
        else:
            print("❌ Tabla company_documents no encontrada")
            return False
        
        # Verificar que ai_configurations no existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'ai_configurations'
            );
        """)
        
        old_table_exists = cursor.fetchone()[0]
        
        if not old_table_exists:
            print("✅ Tabla ai_configurations eliminada correctamente")
        else:
            print("⚠️ Tabla ai_configurations aún existe")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando migración: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MIGRACIÓN: Company Documents Table")
    print("=" * 60)
    print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Ejecutar migración
    success = create_company_documents_table()
    
    if success:
        # Verificar migración
        verify_success = verify_migration()
        
        if verify_success:
            print("\n🎉 ¡Migración completada y verificada exitosamente!")
            print("💡 La tabla company_documents está lista para usar")
        else:
            print("\n⚠️ Migración ejecutada pero la verificación falló")
            sys.exit(1)
    else:
        print("\n❌ Error en la migración")
        sys.exit(1)
    
    print()
    print(f"⏰ Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)