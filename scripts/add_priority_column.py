#!/usr/bin/env python3
"""
Migración: Agregar columna priority a la tabla company_documents
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def add_priority_column():
    """Agregar columna priority a company_documents"""
    
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
        
        print("📋 Iniciando migración: Agregar columna priority...")
        
        # 1. Agregar columna priority si no existe
        print("🔧 Verificando columna priority...")
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'company_documents' AND column_name = 'priority') THEN
                    ALTER TABLE company_documents 
                    ADD COLUMN priority INTEGER NOT NULL DEFAULT 0;
                    RAISE NOTICE 'Columna priority agregada';
                ELSE
                    RAISE NOTICE 'Columna priority ya existe';
                END IF;
            END $$;
        """)
        print("✅ Columna priority verificada/agregada")
        
        # 2. Crear índice para mejor performance (opcional pero recomendado)
        print("🔧 Creando índice en columna priority...")
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_indexes 
                              WHERE tablename = 'company_documents' AND indexname = 'idx_company_documents_priority') THEN
                    CREATE INDEX idx_company_documents_priority ON company_documents(priority);
                    RAISE NOTICE 'Índice en priority creado';
                ELSE
                    RAISE NOTICE 'Índice en priority ya existe';
                END IF;
            END $$;
        """)
        print("✅ Índice en priority verificado/creado")
        
        # 3. Verificar que la columna se creó correctamente
        cursor.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'company_documents' AND column_name = 'priority'
        """)
        
        column_info = cursor.fetchone()
        if column_info:
            print(f"📊 Información de la columna priority:")
            print(f"   • Nombre: {column_info[0]}")
            print(f"   • Tipo: {column_info[1]}")
            print(f"   • Valor por defecto: {column_info[2]}")
            print(f"   • ¿Puede ser nulo?: {column_info[3]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Migración completada exitosamente!")
        print("📝 Columna agregada:")
        print("   • priority (INTEGER) - Valor por defecto: 0")
        print("   • Índice creado para optimizar consultas")
        
    except Exception as e:
        print(f"❌ Error ejecutando migración: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Iniciando migración: add_priority_column...")
    success = add_priority_column()
    if success:
        print("🎉 Migración add_priority_column completada exitosamente!")
    else:
        print("❌ Error en la migración add_priority_column")
        sys.exit(1)