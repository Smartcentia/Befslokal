import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
import app.db.base
from app.domains.core.models.property import Property
from sqlalchemy import select

async def check_address():
    db = SessionLocal()
    try:
        stmt = select(Property).where(Property.name.ilike("%Kompani linge%"))
        result = await db.execute(stmt)
        props = result.scalars().all()
        
        for p in props:
            print(f"Name: '{p.name}'")
            print(f"Address: '{p.address}'")
            
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(check_address())
