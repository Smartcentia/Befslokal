
import sys
import os
import asyncio
from sqlalchemy import select, func

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
# Import all models to ensure registry is populated
import app.db.base

async def check_regions():
    async with SessionLocal() as db:
        result = await db.execute(select(Property.region).distinct())
        regions = result.scalars().all()
        print("Current Regions in DB:")
        for r in regions:
            print(f"- {r}")

if __name__ == "__main__":
    asyncio.run(check_regions())
