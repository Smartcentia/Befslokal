
import asyncio
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property
from app.domains.core.models.party import Party # Ensure Party is registered
from app.domains.hms.models.risk import RiskAssessment # Ensure RiskAssessment is registered
from app.domains.hms.models.internal_control import InternalControlCase # Ensure InternalControlCase is registered
from app.domains.core.models.user import User # Ensure User is registered
from sqlalchemy import select
from sqlalchemy.orm import joinedload

async def check_rents():
    db = SessionLocal()
    try:
        # Fetch a few contracts to inspect 'amount' structure
        stmt = select(Contract).limit(5)
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        print("Inspecting 'amount' field structure:")
        for c in contracts:
            print(f"ID: {c.contract_id}, Amount: {c.amount}")

        # Now try to find 0 rent
        # Assuming amount might be a simple number in JSON or a dict
        
        print("\nChecking for 0 rent in Contracts (programmatically checking all)...")
        stmt_all = select(Contract).options(joinedload(Contract.unit).joinedload(Unit.property))
        result_all = await db.execute(stmt_all)
        all_contracts = result_all.scalars().all()
        
        zero_rent_contracts = []
        for c in all_contracts:
            is_zero = False
            
            # Check structure of amount
            if c.amount is None:
                # None might imply 0 or missing
                pass
            elif isinstance(c.amount, (int, float)) and c.amount == 0:
                is_zero = True
            elif isinstance(c.amount, dict):
                # pattern matching for common rent keys if it is a dict
                # e.g. 'rent', 'value', 'annual'
                # Just dumping whatever keys seem to be 0
                for k, v in c.amount.items():
                    if isinstance(v, (int, float)) and v == 0:
                         # This might be too broad if it catches 'cents': 0
                         pass
                    if k.lower() in ['rent', 'belop', 'amount', 'total'] and v == 0:
                        is_zero = True
                        
            if is_zero:
                prop_name = c.unit.property.name if c.unit and c.unit.property else "Unknown Property"
                zero_rent_contracts.append(f"{prop_name} (Contract: {c.contract_id})")

        if zero_rent_contracts:
            print(f"Found {len(zero_rent_contracts)} contracts with 0 rent:")
            for z in zero_rent_contracts:
                print(z)
        else:
            print("No contracts with explicit 0 rent found in DB.")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(check_rents())
