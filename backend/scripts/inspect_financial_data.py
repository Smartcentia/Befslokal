
import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'KNOWME', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'KNOWME', 'backend', '.env'))

from app.db.session import SessionLocal
# Import ALL models to ensure relationships work
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.center import Center
from app.domains.core.models.party import Party
from app.domains.core.models.user import User
# Also import these just in case
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control

async def inspect():
    try:
        async with SessionLocal() as db:
            print("\n--- PROPERTY FINANCIALS (external_data) ---")
            # Find a property with financials in external_data
            stmt = select(Property).where(Property.external_data.isnot(None)).limit(10)
            result = await db.execute(stmt)
            props = result.scalars().all()
            
            found_financials = False
            for p in props:
                ext = p.external_data or {}
                if 'financials' in ext:
                    print(f"Property: {p.name}")
                    print(f"Financials keys: {ext['financials'].keys()}")
                    if 'manual_expenses' in ext['financials']:
                         expenses = ext['financials']['manual_expenses']
                         if expenses:
                             print("Sample expense entry:", expenses[0])
                             print(f"Total entries: {len(expenses)}")
                             
                             # Identify categories
                             categories = set()
                             for e in expenses:
                                 categories.add(e.get('type'))
                             print(f"Categories found: {categories}")

                    found_financials = True
                    break
            
            if not found_financials:
                print("No properties with 'financials' in external_data found in first 10 analyzed.")

            print("\n--- CONTRACT DATA (amount & costs) ---")
            # Find a contract with amount data
            stmt = select(Contract).limit(5)
            result = await db.execute(stmt)
            contracts = result.scalars().all()
            
            for c in contracts:
                print(f"Contract ID: {c.contract_id}")
                print(f"Status: {c.status}")
                print(f"Category: {c.category}")
                print(f"Amount JSON: {c.amount}")
                print(f"Caretaker Cost: {c.caretaker_cost}")
                print(f"Cleaning Cost: {c.cleaning_cost}")
                print(f"Parking Cost: {c.parking_cost}")
                print("---")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(inspect())
