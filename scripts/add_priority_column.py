#!/usr/bin/env python3
"""
Migracion: Agregar columna priority a la tabla company_documents
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Agregar el directorio raiz al path
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
        
        print("[CLIPBOARD] Iniciando migracion: Agregar columna priority...")
        
        # 1. Agregar columna priority si no existe
        print("[INIT] Verificando columna priority...")
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
        print("[OK] Columna priority verificada/agregada")
        
        # 2. Crear indice para mejor performance (opcional pero recomendado)
        print("[INIT] Creando indice en columna priority...")
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_indexes 
                              WHERE tablename = 'company_documents' AND indexname = 'idx_company_documents_priority') THEN
                    CREATE INDEX idx_company_documents_priority ON company_documents(priority);
                    RAISE NOTICE 'Indice en priority creado';
                ELSE
                    RAISE NOTICE 'Indice en priority ya existe';
                END IF;
            END $$;
        """)
        print("[OK] Indice en priority verificado/creado")
        
        # 3. Verificar que la columna se creo correctamente
        cursor.execute("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'company_documents' AND column_name = 'priority'
        """)
        
        column_info = cursor.fetchone()
        if column_info:
            print(f"[STATS] Informacion de la columna priority:")
            print(f"    Nombre: {column_info[0]}")
            print(f"    Tipo: {column_info[1]}")
            print(f"    Valor por defecto: {column_info[2]}")
            print(f"    Puede ser nulo?: {column_info[3]}")
        
        cursor.close()
        conn.close()
        
        print("\n Migracion completada exitosamente!")
        print(" Columna agregada:")
        print("    priority (INTEGER) - Valor por defecto: 0")
        print("    Indice creado para optimizar consultas")
        
    except Exception as e:
        print(f"[ERR] Error ejecutando migracion: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("[LAUNCH] Iniciando migracion: add_priority_column...")
    success = add_priority_column()
    if success:
        print(" Migracion add_priority_column completada exitosamente!")
    else:
        print("[ERR] Error en la migracion add_priority_column")
        sys.exit(1)