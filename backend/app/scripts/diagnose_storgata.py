
import asyncio
import sys
import os
import json
from sqlalchemy import select, String
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
# Models for registry
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User

async def diagnose():
    print("Diagnosing Storgata...")
    async with SessionLocal() as session:
        # Fetch ALL Storgata properties
        stmt = select(Property).where(Property.name.ilike("%Storgata%"))
        result = await session.execute(stmt)
        props = result.scalars().all()
        
        print(f"Found {len(props)} properties matching 'Storgata'.")
        
        for p in props:
            print(f"Name: {p.name}")
            ext = p.external_data or {}
            fin = ext.get('financials', {})
            print(f"  Financials Keys: {list(fin.keys())}")
            print(f"  Dim 2(T): {fin.get('Dim 2(T)')}")
            print(f"  Dim 2: {fin.get('Dim 2')}")
            
            if str(fin.get('Dim 2(T)')) == '512003':
                print("  MATCH FOUND 512003!")

if __name__ == "__main__":
    asyncio.run(diagnose())
