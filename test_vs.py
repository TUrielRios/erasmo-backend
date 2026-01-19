import asyncio
import os
import sys
sys.path.append(os.getcwd())

from app.db.vector_store import VectorStore
from app.core.config import settings

async def test_init():
    print("Initializing VectorStore...")
    vs = VectorStore()
    await vs.initialize()
    print("VectorStore initialized!")
    await vs.close()
    print("Done")

if __name__ == "__main__":
    asyncio.run(test_init())
