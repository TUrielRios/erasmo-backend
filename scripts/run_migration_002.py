import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Ejecuta la migracion SQL para agregar la tabla de archivos de proyectos"""
    
    print("[REFRESH] Conectando a la base de datos...")
    engine = create_engine(settings.DATABASE_URL)
    
    # Leer el archivo SQL
    print("[DOC] Leyendo archivo de migracion...")
    sql_file = Path(__file__).parent / "002_add_project_files.sql"
    
    print(f"   Buscando archivo en: {sql_file.absolute()}")
    
    if not sql_file.exists():
        print(f"[ERR] Error: No se encontro el archivo {sql_file}")
        print(f"   Ruta absoluta: {sql_file.absolute()}")
        print(f"   Archivos en el directorio:")
        for file in Path(__file__).parent.iterdir():
            print(f"     - {file.name}")
        return False
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    print(f"   Archivo leido: {len(sql_script)} caracteres")
    print(f"   Primeros 100 caracteres: {sql_script[:100]}")
    
    # Ejecutar la migracion
    print(" Ejecutando migracion...")
    try:
        with engine.connect() as conn:
            # Execute the entire script as one transaction
            # This handles DO $$ blocks and other complex SQL properly
            conn.execute(text(sql_script))
            conn.commit()
            print("  [Done] Migracion ejecutada correctamente")
        
        print("\n[OK] Migracion completada exitosamente!")
        print("\nTabla creada:")
        print("  - project_files (archivos de proyectos)")
        print("\nIndices creados:")
        print("  - idx_project_files_project_id")
        print("  - idx_project_files_category")
        print("  - idx_project_files_status")
        print("  - idx_project_files_active")
        print("  - idx_project_files_priority")
        
        return True
        
    except Exception as e:
        print(f"\n[ERR] Error ejecutando migracion: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRACION 002: Agregar Archivos de Proyectos")
    print("=" * 60)
    print()
    
    success = run_migration()
    
    if success:
        print("\n[OK] La migracion se completo correctamente.")
        print("\nAhora puedes:")
        print("  1. Subir archivos a proyectos usando POST /api/v1/projects/{project_id}/files")
        print("  2. Listar archivos con GET /api/v1/projects/{project_id}/files")
        print("  3. Los archivos se procesaran automaticamente y estaran disponibles para la IA")
    else:
        print("\n[ERR] La migracion fallo. Por favor revisa los errores.")