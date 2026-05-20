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

async def verify_empty_elements():
    db = SessionLocal()
    try:
        # Get properties where external_data has 'elements' key
        stmt = select(Property).limit(200)
        result = await db.execute(stmt)
        props = result.scalars().all()
        
        count_elements_key = 0
        count_elements_val = 0
        
        for p in props:
            if p.external_data and isinstance(p.external_data, dict):
                # Search for key
                if 'elements' in p.external_data:
                    count_elements_key += 1
                    val = p.external_data['elements']
                    if val:
                        print(f"FOUND DATA! Property: {p.name}, Value: {val}")
                        count_elements_val += 1
                
                # Also check 'master_data' -> 'elements'
                if 'master_data' in p.external_data:
                    md = p.external_data['master_data']
                    if 'elements' in md:
                        count_elements_key += 1
                        val = md['elements']
                        if val:
                           print(f"FOUND DATA (nested)! Property: {p.name}, Value: {val}")
                           count_elements_val += 1
        
        print(f"Scanned {len(props)} properties.")
        print(f"Found 'elements' KEY in {count_elements_key} records.")
        print(f"Found 'elements' VALUE in {count_elements_val} records.")
                
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(verify_empty_elements())
