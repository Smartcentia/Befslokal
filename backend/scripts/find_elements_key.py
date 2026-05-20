import asyncio
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
import app.db.base
from app.domains.core.models.property import Property
from sqlalchemy import select

def find_key_recursive(data, target_value_pattern, current_path=""):
    found = []
    if isinstance(data, dict):
        for k, v in data.items():
            new_path = f"{current_path}.{k}" if current_path else k
            if "elements" in k.lower() or "arkiv" in k.lower():
                 if v: # Only keep truthy values
                     found.append((new_path, v))
            
            found.extend(find_key_recursive(v, target_value_pattern, new_path))
    elif isinstance(data, list):
         for i, item in enumerate(data):
             new_path = f"{current_path}[{i}]"
             found.extend(find_key_recursive(item, target_value_pattern, new_path))
             
    return found

async def find_elements_key():
    db = SessionLocal()
    try:
        # Get properties with external_data
        stmt = select(Property).where(Property.external_data.is_not(None)).limit(50)
        result = await db.execute(stmt)
        props = result.scalars().all()
        
        print("Scannning for 'elements' keys...")
        for p in props:
            matches = find_key_recursive(p.external_data, "")
            if matches:
                print(f"Property: {p.name}")
                for path, val in matches:
                    print(f"  Key Path: {path} -> Value: {val}")
                print("-" * 20)
                
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(find_elements_key())
