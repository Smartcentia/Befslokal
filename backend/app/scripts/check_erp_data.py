import sys
import os
import asyncio
from sqlalchemy import select
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property

async def check_data():
    async with SessionLocal() as db:
        res = await db.execute(select(Property).where(Property.unit_id_erp != None))
        props = res.scalars().all()
        print(f"Properties with unit_id_erp: {len(props)}")
        if props:
            for p in props[:5]:
                print(f"Property: {p.name}, unit_id_erp: {p.unit_id_erp}")
        
        res_all = await db.execute(select(Property))
        all_props = res_all.scalars().all()
        print(f"Total properties: {len(all_props)}")

if __name__ == "__main__":
    asyncio.run(check_data())
