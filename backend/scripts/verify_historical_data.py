
import asyncio
import os
import sys
import json
from sqlalchemy import select, text
from sqlalchemy.orm import joinedload
import pprint

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'KNOWME', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'KNOWME', 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
# Import dependencies just in case
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.center import Center
from app.domains.core.models.party import Party
from app.domains.core.models.user import User
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control


async def verify():
    async with SessionLocal() as db:
        print("\n--- VERIFYING HISTORICAL DATA ---")
        
        # Check count
        stmt = text("SELECT count(*) FROM properties WHERE external_data->'financial_history' IS NOT NULL")
        result = await db.execute(stmt)
        count = result.scalar()
        print(f"Properties with 'financial_history': {count}")
        
        if count == 0:
            print("❌ No data generation detected.")
            return

        # Get one valid property
        stmt = select(Property).where(text("external_data->'financial_history' IS NOT NULL")).limit(1)
        result = await db.execute(stmt)
        prop = result.scalars().first()
        
        print(f"Property: {prop.name} (ID: {prop.property_id})")
        ext = prop.external_data
        history = ext.get('financial_history')

        print("✅ 'financial_history' found!")
        print(f"Years found: {sorted(history.keys())}")
        
        # Check integrity of 2024 data
        y23 = history.get('2024')
        if y23:
            print("\n--- Sample Data (2024) ---")
            print(f"Rent: {y23.get('rent')}")
            print(f"Total Costs: {y23.get('total_costs')}")
            print(f"Expense count: {len(y23.get('expenses', []))}")
        
        # Check trend (2024 vs 2021)
        y23 = history.get('2024')
        y20 = history.get('2021')
        if y23 and y20:
             print("\n--- Trend Check ---")
             rent24 = y23.get('rent', 0)
             rent21 = y20.get('rent', 0)
             print(f"Rent 2024: {rent24:,.0f}")
             print(f"Rent 2021: {rent21:,.0f}")
             
             if rent24 > rent21:
                 print("✅ Trend OK: 2024 rent > 2021 rent (Inflation logic working)")
             else:
                 print("⚠️ Trend Warning: 2024 rent <= 2021 rent (Might be correct due to noise, but check logic)")


if __name__ == "__main__":
    asyncio.run(verify())
