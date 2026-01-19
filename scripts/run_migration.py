"""
Script to run database migrations
Usage: python scripts/run_migration.py
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Run the SQL migration script"""
    engine = create_engine(settings.DATABASE_URL)
    
    # Read the SQL file
    sql_file = Path(__file__).parent / "001_add_projects_and_sharing.sql"
    
    with open(sql_file, 'r') as f:
        sql_script = f.read()
    
    # Execute the migration
    with engine.connect() as conn:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        
        for statement in statements:
            if statement:
                try:
                    conn.execute(text(statement))
                    print(f"[Done] Executed: {statement[:50]}...")
                except Exception as e:
                    print(f" Error executing statement: {statement[:50]}...")
                    print(f"  Error: {e}")
                    raise
        
        conn.commit()
    
    print("\n[Done] Migration completed successfully!")

if __name__ == "__main__":
    print("Running database migration...")
    print("=" * 50)
    run_migration()
