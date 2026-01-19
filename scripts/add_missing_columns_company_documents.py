#!/usr/bin/env python3
"""
Migracion: Agregar todas las columnas faltantes a la tabla company_documents
Incluye: priority, processing_status, processed_chunks, total_chunks, error_message,
         processing_started_at, processing_completed_at
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime

# Agregar el directorio raiz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def add_missing_columns_company_documents():
    """Agregar todas las columnas faltantes a company_documents"""
    
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
        
        print("[CLIPBOARD] Iniciando migracion: Agregar columnas faltantes a company_documents...")
        
        # 1. Crear tipo ENUM processingstatus si no existe
        print("[INIT] Verificando tipo ENUM processingstatus...")
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'processingstatus') THEN
                    CREATE TYPE processingstatus AS ENUM ('pending', 'processing', 'completed', 'failed');
                    RAISE NOTICE 'Tipo ENUM processingstatus creado';
                ELSE
                    RAISE NOTICE 'Tipo ENUM processingstatus ya existe';
                END IF;
            END $$;
        """)
        print("[OK] Tipo ENUM processingstatus verificado/creado")
        
        # Lista de columnas a agregar con sus definiciones
        columns_to_add = [
            {
                'name': 'priority',
                'definition': 'INTEGER NOT NULL DEFAULT 0',
                'description': 'Prioridad del documento para ordenamiento'
            },
            {
                'name': 'processing_status',
                'definition': 'processingstatus NOT NULL DEFAULT \'pending\'',
                'description': 'Estado del procesamiento del documento'
            },
            {
                'name': 'processed_chunks',
                'definition': 'INTEGER DEFAULT 0',
                'description': 'Numero de chunks procesados'
            },
            {
                'name': 'total_chunks',
                'definition': 'INTEGER DEFAULT 0',
                'description': 'Numero total de chunks a procesar'
            },
            {
                'name': 'error_message',
                'definition': 'TEXT',
                'description': 'Mensaje de error si el procesamiento falla'
            },
            {
                'name': 'processing_started_at',
                'definition': 'TIMESTAMP WITH TIME ZONE',
                'description': 'Fecha/hora de inicio del procesamiento'
            },
            {
                'name': 'processing_completed_at',
                'definition': 'TIMESTAMP WITH TIME ZONE',
                'description': 'Fecha/hora de finalizacion del procesamiento'
            }
        ]
        
        # 2. Agregar cada columna si no existe
        for column in columns_to_add:
            print(f"[INIT] Verificando columna {column['name']}...")
            cursor.execute(f"""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                  WHERE table_name = 'company_documents' AND column_name = '{column['name']}') THEN
                        ALTER TABLE company_documents 
                        ADD COLUMN {column['name']} {column['definition']};
                        RAISE NOTICE 'Columna {column['name']} agregada';
                    ELSE
                        RAISE NOTICE 'Columna {column['name']} ya existe';
                    END IF;
                END $$;
            """)
            print(f"[OK] Columna {column['name']} verificada/agregada")
        
        # 3. Crear indices para mejor performance
        print("[INIT] Creando indices...")
        indexes_to_create = [
            ('idx_company_documents_priority', 'priority'),
            ('idx_company_documents_processing_status', 'processing_status'),
            ('idx_company_documents_processed_chunks', 'processed_chunks'),
            ('idx_company_documents_is_active', 'is_active')
        ]
        
        for index_name, column_name in indexes_to_create:
            cursor.execute(f"""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_indexes 
                                  WHERE tablename = 'company_documents' AND indexname = '{index_name}') THEN
                        CREATE INDEX {index_name} ON company_documents({column_name});
                        RAISE NOTICE 'Indice {index_name} creado';
                    ELSE
                        RAISE NOTICE 'Indice {index_name} ya existe';
                    END IF;
                END $$;
            """)
            print(f"[OK] Indice {index_name} verificado/creado")
        
        # 4. Verificar que todas las columnas se crearon correctamente
        print("[SEARCH] Verificando columnas existentes...")
        cursor.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'company_documents'
            ORDER BY column_name
        """)
        
        all_columns = cursor.fetchall()
        print("\n[STATS] Columnas actuales en company_documents:")
        for column in all_columns:
            print(f"    {column[0]} ({column[1]}) - Default: {column[2]} - Nullable: {column[3]}")
        
        cursor.close()
        conn.close()
        
        print("\n Migracion completada exitosamente!")
        print(" Columnas agregadas:")
        for column in columns_to_add:
            print(f"    {column['name']} - {column['description']}")
        print("[STATS] Indices creados para optimizar consultas")
        
    except Exception as e:
        print(f"[ERR] Error ejecutando migracion: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("[LAUNCH] Iniciando migracion: add_missing_columns_company_documents...")
    success = add_missing_columns_company_documents()
    if success:
        print(" Migracion completada exitosamente!")
    else:
        print("[ERR] Error en la migracion")
        sys.exit(1)