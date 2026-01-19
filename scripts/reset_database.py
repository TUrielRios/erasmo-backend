#!/usr/bin/env python3
"""
Script para reiniciar la base de datos completamente
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Agregar el directorio raiz al path para importar settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ahora intentar importar settings
try:
    from app.core.config import settings
except ImportError:
    # Si falla, usar variables de entorno o valores por defecto
    import os
    settings = type('obj', (object,), {
        'DATABASE_HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'DATABASE_PORT': os.getenv('DATABASE_PORT', '5432'),
        'DATABASE_NAME': os.getenv('DATABASE_NAME', 'erasmo_db'),
        'DATABASE_USER': os.getenv('DATABASE_USER', 'postgres'),
        'DATABASE_PASSWORD': os.getenv('DATABASE_PASSWORD', 'postgres')
    })()

def reset_database():
    """Reiniciar la base de datos completamente"""
    
    try:
        print(" Conectando a PostgreSQL...")
        print(f"   Host: {settings.DATABASE_HOST}")
        print(f"   Puerto: {settings.DATABASE_PORT}")
        print(f"   Usuario: {settings.DATABASE_USER}")
        print(f"   Base de datos: {settings.DATABASE_NAME}")
        
        # Conectar a PostgreSQL (sin especificar base de datos)
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("[DELETE]  Reiniciando base de datos...")
        
        # Terminar conexiones existentes a la base de datos
        print("   [REFRESH] Terminando conexiones existentes...")
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{settings.DATABASE_NAME}'
            AND pid <> pg_backend_pid();
        """)
        
        # Eliminar y recrear la base de datos
        print("   [DELETE]  Eliminando base de datos...")
        cursor.execute(f"DROP DATABASE IF EXISTS {settings.DATABASE_NAME};")
        
        print("    Creando nueva base de datos...")
        cursor.execute(f"CREATE DATABASE {settings.DATABASE_NAME};")
        
        print("[OK] Base de datos reiniciada exitosamente!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERR] Error reiniciando base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("[LAUNCH] Iniciando reinicio de base de datos...")
    success = reset_database()
    if success:
        print("\n Base de datos reiniciada. Ahora ejecuta:")
        print("   alembic upgrade head  # Para crear todas las tablas")
        print("   o")
        print("   python scripts/seed_data.py  # Si tienes datos de prueba")
    else:
        print("[ERR] Error reiniciando base de datos")
        sys.exit(1)