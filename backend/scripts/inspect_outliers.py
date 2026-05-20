
import asyncio
import sys
import os
from sqlalchemy import select
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.user import User
from app.domains.core.models.party import Party
# Then Property
from app.domains.core.models.property import Property

async def inspect():
    print("Inspecting Anomalies...")
    async with SessionLocal() as db:
        # Fetch Skatval
        stmt = select(Property).where(Property.name.ilike('%Skatval%'))
        result = await db.execute(stmt)
        props = result.scalars().all()
        
        for p in props:
            print(f"Property: {p.name} (ID: {p.property_id})")
            expenses = p.external_data.get('financials', {}).get('manual_expenses', [])
            
            # Sort by amount desc
            expenses.sort(key=lambda x: float(x.get('amount', 0)), reverse=True)
            
            print("Top 5 Highest Expenses:")
            for e in expenses[:5]:
                print(f"  - Amount: {e.get('amount')}")
                print(f"    Source: {e.get('source')}")
                print(f"    Raw: {e}")
                print("-" * 20)

if __name__ == "__main__":
    asyncio.run(inspect())
