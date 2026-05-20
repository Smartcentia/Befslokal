
import asyncio
import sys
import os
import json
from dotenv import load_dotenv
from sqlalchemy import select, func

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Load env
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal

# Import related models to ensure SQLAlchemy registry is populated
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
from app.domains.core.models.user import User
# Then Property
from app.domains.core.models.property import Property

async def main():
    print("Verifying stored data for recent imports...")
    async with SessionLocal() as db:
        # Count ALL properties with financial data
        print("Calculating system-wide enrichment totals...")
        
        stmt = select(Property.property_id, Property.external_data).where(
             Property.external_data.is_not(None)
        )
        
        result = await db.execute(stmt)
        all_props = result.all()
        
        enriched_count = 0
        total_transactions = 0
        
        for pid, ext in all_props:
            if not ext: continue
            fin = ext.get('financials', {})
            manual = fin.get('manual_expenses', [])
            if manual:
                enriched_count += 1
                total_transactions += len(manual)
                
        print("-" * 50)
        print(f"TOTAL VERIFICATION SUMMARY (Files 01-14)")
        print(f"Properties Enriched: {enriched_count}")
        print(f"Total Transactions Stored: {total_transactions}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
