import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from app.db.session import SessionLocal
from sqlalchemy import select, text
from app.domains.core.models.property import Property

async def check_data():
    async with SessionLocal() as db:
        print("Checking database connection...")
        try:
            # Check properties
            result = await db.execute(select(Property))
            props = result.scalars().all()
            print(f"Found {len(props)} properties in database.")
            if props:
                print(f"Sample: {props[0].address} ({props[0].property_id})")
            else:
                print("Properties table is empty!")
                
            # Check tables existence in PostgreSQL
            result = await db.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';"))
            tables = result.scalars().all()
            print(f"Tables found: {tables}")
            
        except Exception as e:
            print(f"Error querying database: {e}")

if __name__ == "__main__":
    asyncio.run(check_data())
