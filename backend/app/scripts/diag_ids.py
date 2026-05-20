import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from dotenv import load_dotenv

# Path setup
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property

async def diagnostic():
    target_loks = ["1217", "2335", "3608", "3522", "5107", "5957", "1214"]
    print(f"Checking database for Lokasjonskoder: {target_loks}")
    
    async with SessionLocal() as db:
        # Check by strict string
        for lok in target_loks:
            # Check for both exact and with .0 just in case
            stmt = select(Property).where(Property.lokalisering_id.in_([lok, lok + ".0"]))
            result = await db.execute(stmt)
            props = result.scalars().all()
            
            if not props:
                print(f"LOK {lok}: NOT FOUND in database.")
                continue
                
            for p in props:
                print(f"LOK {lok} (stored as '{p.lokalisering_id}'):")
                print(f"  - Name: {p.name}")
                print(f"  - unit_id_erp: '{p.unit_id_erp}'")
                print(f"  - address: {p.address}")
                print(f"  - property_id: {p.property_id}")

if __name__ == "__main__":
    asyncio.run(diagnostic())
