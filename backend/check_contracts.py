import asyncio
from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.db.base import Base
from app.domains.core.models.contract import Contract

async def count_contracts():
    async with SessionLocal() as db:
        result = await db.execute(select(func.count(Contract.contract_id)))
        count = result.scalar()
        print(f"Total contracts: {count}")
        
        if count > 0:
            result = await db.execute(select(Contract).limit(5))
            contracts = result.scalars().all()
            for c in contracts:
                print(f"Contract: {c.contract_id}, Status: {c.status}")

if __name__ == "__main__":
    asyncio.run(count_contracts())
