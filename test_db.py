import sys
import os
# Add current directory to path to import app
sys.path.append(os.getcwd())

from app.core.config import settings
from sqlalchemy import create_engine
import time

print(f"Connecting to: {settings.DATABASE_URL.split('@')[-1]}") # Hide credentials
try:
    engine = create_engine(settings.DATABASE_URL, connect_args={'connect_timeout': 5})
    start = time.time()
    with engine.connect() as conn:
        print(f"Connected in {time.time() - start:.2f}s")
    print("Database connection SUCCESSFUL")
except Exception as e:
    print(f"Database connection FAILED: {e}")
