import asyncio
from app.db.session import SessionLocal as async_session_maker
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
from app.domains.core.models.property import Property
import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import select


async def main():
    async with async_session_maker() as db:
        result = await db.execute(select(Contract).limit(5))
        contracts = result.scalars().all()
        
        print(f"Found {len(contracts)} contracts.")
        for c in contracts:
            print(f"ID: {c.contract_id}")
            print(f"External Data: {c.external_data}")
            if c.external_data and 'contract_number' in c.external_data:
                print(f"  -> Found contract_number in external_data: {c.external_data['contract_number']}")
            else:
                print("  -> contract_number NOT found in external_data")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(main())
