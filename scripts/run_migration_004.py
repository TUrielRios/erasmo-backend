"""
Script to run database migration for adding protocols table
Usage: python scripts/run_migration_004.py
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Run the SQL migration script to add protocols table"""
    engine = create_engine(settings.DATABASE_URL)
    
    # Read the SQL file
    sql_file = Path(__file__).parent / "add_protocols_table.sql"
    
    print(f"Reading migration file: {sql_file}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Execute the migration
    with engine.connect() as conn:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        
        print(f"\nExecuting {len(statements)} statements...\n")
        
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    # Execute the statement
                    result = conn.execute(text(statement))
                    
                    # Show preview of statement
                    preview = statement.replace('\n', ' ')[:80]
                    print(f"✓ [{i}/{len(statements)}] Executed: {preview}...")
                    
                    # If it's a SELECT statement, show results
                    if statement.strip().upper().startswith('SELECT'):
                        rows = result.fetchall()
                        if rows:
                            print("  Results:")
                            for row in rows:
                                print(f"    {dict(row._mapping)}")
                        else:
                            print("  No results returned")
                    
                except Exception as e:
                    print(f"✗ [{i}/{len(statements)}] Error executing statement:")
                    print(f"  Statement: {statement[:100]}...")
                    print(f"  Error: {e}")
                    # Don't raise on "already exists" errors
                    if "already exists" not in str(e).lower():
                        raise
                    else:
                        print("  (Skipping - already exists)")
        
        conn.commit()
    
    print("\n" + "=" * 50)
    print("✓ Migration completed successfully!")
    print("=" * 50)
    print("\nChanges applied:")
    print("  Table created:")
    print("    - protocols")
    print("  Columns added to 'company_documents':")
    print("    - protocol_id (INTEGER, FK to protocols)")
    print("    - use_protocol (BOOLEAN, default: FALSE)")
    print("  Indexes created:")
    print("    - idx_protocols_name")
    print("    - idx_protocols_category")
    print("    - idx_protocols_is_active")
    print("    - idx_company_documents_protocol_id")

if __name__ == "__main__":
    print("=" * 50)
    print("Running database migration: Add Protocols Table")
    print("=" * 50)
    print()
    run_migration()
