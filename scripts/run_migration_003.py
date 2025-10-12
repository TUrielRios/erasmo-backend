"""
Script to run database migration for adding message columns
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
    """Run the SQL migration script to add message columns"""
    engine = create_engine(settings.DATABASE_URL)
    
    # Read the SQL file
    sql_file = Path(__file__).parent / "add_message_columns.sql"
    
    print(f"Reading migration file: {sql_file}")
    
    with open(sql_file, 'r') as f:
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
                    raise
        
        conn.commit()
    
    print("\n" + "=" * 50)
    print("✓ Migration completed successfully!")
    print("=" * 50)
    print("\nColumns added to 'messages' table:")
    print("  - updated_at (TIMESTAMP WITH TIME ZONE)")
    print("  - is_edited (BOOLEAN, default: FALSE)")
    print("  - message_metadata (TEXT)")
    print("\nIndex created:")
    print("  - idx_messages_updated_at")

if __name__ == "__main__":
    print("=" * 50)
    print("Running database migration: Add Message Columns")
    print("=" * 50)
    print()
    run_migration()