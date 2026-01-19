#!/usr/bin/env python3
"""
Migracion: Agregar columnas category y description a la tabla company_documents
Incluye creacion de tipo ENUM documentcategory
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Agregar el directorio raiz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def add_category_description_columns():
    """Agregar columnas category y description a company_documents"""
    
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
        
        print("[CLIPBOARD] Iniciando migracion: Agregar columnas category y description...")
        
        # 1. Crear tipo ENUM documentcategory si no existe
        print("[INIT] Verificando tipo ENUM documentcategory...")
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'documentcategory') THEN
                    CREATE TYPE documentcategory AS ENUM ('knowledge_base', 'policy', 'procedure', 'manual', 'other');
                    RAISE NOTICE 'Tipo ENUM documentcategory creado';
                ELSE
                    RAISE NOTICE 'Tipo ENUM documentcategory ya existe';
                END IF;
            END $$;
        """)
        print("[OK] Tipo ENUM documentcategory verificado/creado")
        
        # 2. Agregar columna category si no existe
        print("[INIT] Verificando columna category...")
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'category') THEN
                    ALTER TABLE company_documents ADD COLUMN category documentcategory NOT NULL DEFAULT 'knowledge_base';
                    RAISE NOTICE 'Columna category agregada';
                ELSE
                    RAISE NOTICE 'Columna category ya existe';
                END IF;
            END $$;
        """)
        print("[OK] Columna category verificada/agregada")
        
        # 3. Agregar columna description si no existe
        print("[INIT] Verificando columna description...")
        cursor.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'company_documents' AND column_name = 'description') THEN
                    ALTER TABLE company_documents ADD COLUMN description TEXT;
                    RAISE NOTICE 'Columna description agregada';
                ELSE
                    RAISE NOTICE 'Columna description ya existe';
                END IF;
            END $$;
        """)
        print("[OK] Columna description verificada/agregada")
        
        # 4. Actualizar registros existentes
        print("[REFRESH] Actualizando registros existentes...")
        cursor.execute("""
            UPDATE company_documents 
            SET category = 'knowledge_base' 
            WHERE category IS NULL
        """)
        affected_rows = cursor.rowcount
        print(f"[OK] {affected_rows} registros actualizados")
        
        cursor.close()
        conn.close()
        
        print("\n Migracion completada exitosamente!")
        print(" Columnas agregadas:")
        print("    category (documentcategory ENUM)")
        print("    description (TEXT)")
        print("[STATS] Valores ENUM disponibles: 'knowledge_base', 'policy', 'procedure', 'manual', 'other'")
        
    except Exception as e:
        print(f"[ERR] Error ejecutando migracion: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("[LAUNCH] Iniciando migracion: add_category_description_columns...")
    success = add_category_description_columns()
    if success:
        print(" Migracion add_category_description_columns completada exitosamente!")
    else:
        print("[ERR] Error en la migracion add_category_description_columns")
        sys.exit(1)