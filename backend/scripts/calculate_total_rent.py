
import sys
import os
import asyncio
from sqlalchemy import select

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
import app.db.base # Register all models
from app.domains.core.models.contract import Contract

async def calculate_total():
    async with SessionLocal() as db:
        stmt = select(Contract).where(Contract.status == 'active')
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        total_rent = 0.0
        count = 0
        
        for c in contracts:
            if isinstance(c.amount, dict):
                val = c.amount.get('amount_per_year', 0)
                try:
                    val_float = float(val)
                    # Exclude insane values just in case some slipped through or 0s
                    if val_float < 100_000_000: 
                        total_rent += val_float
                        count += 1
                except:
                    pass
                    
        print(f"Total Active Contracts: {count}")
        print(f"Total Annual Rent: {total_rent:,.2f}")

if __name__ == "__main__":
    asyncio.run(calculate_total())
