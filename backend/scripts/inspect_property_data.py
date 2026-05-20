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

async def inspect_property_data():
    db = SessionLocal()
    try:
        # Get a property with external_data
        stmt = select(Property).where(Property.external_data.is_not(None)).limit(1)
        result = await db.execute(stmt)
        prop = result.scalars().first()
        
        if prop:
            print(f"Property: {prop.name}")
            print(json.dumps(prop.external_data, indent=2))
        else:
            print("No properties with external_data found.")
                
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(inspect_property_data())
