
import sys
import os
import chromadb
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.config import settings

def inspect_chromadb():
    chroma_path = Path(settings.CHROMA_DB_PATH)
    if not chroma_path.exists():
        print(f"ChromaDB path does not exist: {chroma_path}")
        return

    print(f"Inspecting ChromaDB at: {chroma_path}")
    client = chromadb.PersistentClient(path=str(chroma_path))
    
    collections = client.list_collections()
    print(f"Found {len(collections)} collections.")
    
    for col in collections:
        print(f"\nCollection Name: {col.name}")
        print(f"Count: {col.count()}")
        
        if col.count() > 0:
            peek = col.peek(limit=5)
            print("Sample Metadata:")
            for meta in peek['metadatas']:
                print(f" - {meta}")
        else:
            print(" (Empty)")

if __name__ == "__main__":
    inspect_chromadb()
