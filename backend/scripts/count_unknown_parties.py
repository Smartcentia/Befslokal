
import sys
import os
import asyncio
from sqlalchemy import select, func

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party

async def count_unknown():
    async with SessionLocal() as db:
        # Standard placeholder name from import script
        placeholder_name = "Ukjent Leietaker (Masterdata)"
        
        # Find the party
        stmt = select(Party).where(Party.name == placeholder_name)
        result = await db.execute(stmt)
        party = result.scalars().first()
        
        if not party:
            print(f"Party '{placeholder_name}' not found.")
            # Check for ANY contracts without party or with other placeholders?
            # Let's check total contracts and how many have ANY party
            stmt_all = select(func.count(Contract.contract_id))
            total = (await db.execute(stmt_all)).scalar() or 0
            print(f"Total Contracts: {total}")
            return

        # Count contracts linked to this party
        stmt_count = select(func.count(Contract.contract_id)).where(Contract.party_id == party.party_id)
        count = (await db.execute(stmt_count)).scalar() or 0
        
        # Also count contracts with NO party
        stmt_none = select(func.count(Contract.contract_id)).where(Contract.party_id == None)
        count_none = (await db.execute(stmt_none)).scalar() or 0
        
        print(f"Contracts linked to '{placeholder_name}': {count}")
        print(f"Contracts with NO landlord: {count_none}")
        
        # Total active contracts
        stmt_active = select(func.count(Contract.contract_id)).where(Contract.status == 'active')
        count_active = (await db.execute(stmt_active)).scalar() or 0
        print(f"Total Active Contracts: {count_active}")

if __name__ == "__main__":
    asyncio.run(count_unknown())
