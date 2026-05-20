import asyncio
import os
import sys
from sqlalchemy import select

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from backend.app.db.session import SessionLocal
from backend.app.domains.core.models.property import Property
from backend.app.domains.core.models.contract import Contract
from backend.app.domains.core.models.unit import Unit
from backend.app.domains.core.models.party import Party
# Import related models for mapper initialization
from backend.app.domains.hms.models.risk import RiskAssessment
from backend.app.domains.hms.models.internal_control import InternalControlCase
from backend.app.domains.core.models.user import User

async def check():
    async with SessionLocal() as s:
        print("Checking Name for 'Snyta'...")
        res = await s.execute(select(Property).where(Property.name.ilike('%Snyta%')))
        for p in res.scalars():
            print(f"Found NAME match: {p.name} | {p.address}")
            
        print("\nChecking Address for 'Askveien'...")
        res = await s.execute(select(Property).where(Property.address.ilike('%Askveien%')))
        for p in res.scalars():
            print(f"Found ADDRESS match: {p.name} | {p.address}")

if __name__ == "__main__":
    asyncio.run(check())
