import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
import app.db.base # Registers all models
from app.domains.core.models.contract import Contract
from sqlalchemy import select

from sqlalchemy import update

async def setup_test_data():
    db = SessionLocal()
    try:
        # Find a contract
        result = await db.execute(select(Contract).limit(1))
        contract = result.scalars().first()
        
        if not contract:
            print("No contracts found in database.")
            return
            
        print(f"Found contract: {contract.contract_id}")
        contract_id = contract.contract_id
        
        # Update elements field using direct update statement
        stmt = update(Contract).where(Contract.contract_id == contract_id).values(elements="TEST-ELEMENTS-123")
        await db.execute(stmt)
        await db.commit()
        
        print(f"Updated contract {contract_id} with elements='TEST-ELEMENTS-123'")
        print(f"URL to check: http://localhost:3000/contracts/{contract_id}")
        return str(contract_id)
        
    except Exception as e:
        print(f"Error: {e}")
        await db.rollback()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(setup_test_data())
