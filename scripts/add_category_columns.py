#!/usr/bin/env python3
"""
Migracion: Agregar columna category a la tabla company_documents
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Agregar el directorio raiz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def add_category_column():
    """Agregar columna category a company_documents"""
    
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
        
        print("[CLIPBOARD] Iniciando migracion: Agregar columna category...")
        
        # Verificar si la columna ya existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'company_documents' 
            AND column_name = 'category'
        """)
        
        if cursor.fetchone():
            print("[OK] La columna 'category' ya existe en la tabla company_documents")
            return True
        
        print("[INIT] Agregando columna category a company_documents...")
        
        # Agregar columna category
        cursor.execute("""
            ALTER TABLE company_documents 
            ADD COLUMN category VARCHAR(50) NOT NULL DEFAULT 'knowledge_base'
        """)
        
        print("[OK] Columna category agregada exitosamente")
        
        # Actualizar registros existentes (por si hay valores NULL)
        print("[REFRESH] Actualizando registros existentes...")
        cursor.execute("""
            UPDATE company_documents 
            SET category = 'knowledge_base' 
            WHERE category IS NULL
        """)
        
        print("[OK] Registros existentes actualizados")
        
        cursor.close()
        conn.close()
        
        print("\n Migracion completada exitosamente!")
        
    except Exception as e:
        print(f"[ERR] Error ejecutando migracion: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("[LAUNCH] Iniciando migracion: add_category_column...")
    success = add_category_column()
    if success:
        print(" Migracion add_category_column completada exitosamente!")
    else:
        print("[ERR] Error en la migracion add_category_column")
        sys.exit(1)