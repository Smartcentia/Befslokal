import asyncio
import os
import sys
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add the project root and backend to the python path
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

async def verify_quality():
    async with SessionLocal() as session:
        # Check Specific Property Ringerike/Snyta
        print("\n=== Targeted Check (Snyta) ===")
        stmt = select(Property).where(Property.name.ilike("%Snyta%"))
        result = await session.execute(stmt)
        p = result.scalars().first()
        
        if p:
            print(f"Name: {p.name}")
            print(f"  Region: {p.region}")
            print(f"  City: {p.city}")
            print(f"  Postal: {p.postal_code}")
            
            # Check Contract
            stmt = (
                select(Contract)
                .join(Unit, Contract.unit_id == Unit.unit_id)
                .where(Unit.property_id == p.property_id)
            )
            result = await session.execute(stmt)
            c = result.scalars().first()
            if c:
                print(f"  Contract Status: {c.status}")
                print(f"  Contract End Date: {c.end_date}")
                if c.end_date is None:
                    print("SUCCESS: Indefinite contract correctly identified.")
                else:
                    print("NOTE: Contract has an end date. checking if it should be indefinite...")
        else:
            print("FAILURE: Ringerike property not found in DB!")

if __name__ == "__main__":
    asyncio.run(verify_quality())
