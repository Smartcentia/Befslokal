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
from app.domains.core.models.contract import Contract
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from sqlalchemy import select, text

async def deep_scan_jsonb():
    db = SessionLocal()
    try:
        # 1. Search for keys like 'elements', 'arkiv', 'saksnr' in JSONB columns
        keywords = ['elements', 'arkiv', 'sak', 'ref']
        
        print("--- Scanning Contract.external_data ---")
        stmt = select(Contract).limit(100)
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        found_in_contract = False
        for c in contracts:
            if c.external_data:
                data_str = json.dumps(c.external_data).lower()
                for kw in keywords:
                    if kw in data_str:
                        print(f"MATCH in Contract {c.contract_id}: Found '{kw}'")
                        print(f"  Data snippet: {data_str[:200]}...")
                        found_in_contract = True
                        
        if not found_in_contract:
            print("No keyword matches in sample Contract external_data.")

        print("\n--- Scanning Property.external_data ---")
        stmt = select(Property).limit(100)
        result = await db.execute(stmt)
        props = result.scalars().all()
        
        found_in_prop = False
        for p in props:
            if p.external_data:
                data_str = json.dumps(p.external_data).lower()
                for kw in keywords:
                    if kw in data_str:
                        print(f"MATCH in Property {p.name}: Found '{kw}'")
                        # print(f"  Data snippet: {data_str[:200]}...")
                        found_in_prop = True
                        
        if not found_in_prop:
            print("No keyword matches in sample Property external_data.")
            
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(deep_scan_jsonb())
