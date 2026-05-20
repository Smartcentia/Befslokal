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
from app.domains.core.models.contract import Contract
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from sqlalchemy.orm import joinedload
from sqlalchemy import select, and_

# ... import other things

async def analyze_elements_source():
    db = SessionLocal()
    try:
        # Check 1: Contracts with 'elements' in external_data
        print("--- Analyzing Contracts external_data ---")
        stmt = select(Contract).where(Contract.external_data.is_not(None))
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        elements_in_ext = 0
        for c in contracts:
            if c.external_data and ('elements' in c.external_data or 'arkivreferanse' in c.external_data):
                elements_in_ext += 1
                
        print(f"Contracts with 'elements'/'arkivreferanse' in external_data: {elements_in_ext} / {len(contracts)}")

        # Check 2: Contracts via Unit -> Property -> external_data.master_data.archive_name
        print("\\n--- Analyzing Property Fallback (archive_name) ---")
        # Get all contracts with units and properties
        stmt = select(Contract).join(Contract.unit).join(Unit.property).options(
            joinedload(Contract.unit).joinedload(Unit.property)
        )
        result = await db.execute(stmt)
        contracts_with_prop = result.scalars().all()
        
        potential_backfill = 0
        examples = []
        
        for c in contracts_with_prop:
            prop = c.unit.property
            if prop and prop.external_data:
                # Check known paths
                master_data = prop.external_data.get('master_data', {})
                archive_name = master_data.get('archive_name')
                
                if archive_name:
                    potential_backfill += 1
                    if len(examples) < 3:
                        examples.append(f"Contract {c.contract_id} -> Property {prop.name}: {archive_name}")
                        
        print(f"Contracts that could receive data from Property.archive_name: {potential_backfill} / {len(contracts_with_prop)}")
        if examples:
            print("Examples:")
            for ex in examples:
                print(f"  {ex}")
                
    finally:
        await db.close()
        await db.close()

if __name__ == "__main__":
    asyncio.run(analyze_elements_source())
