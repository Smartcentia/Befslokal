import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
import app.db.base
from app.domains.core.models.contract import Contract
from sqlalchemy import update

async def cleanup_test_data():
    db = SessionLocal()
    try:
        # Revert elements field for the test contract
        contract_id = "3af5ce8c-4056-44e4-8831-449ea28f7499"
        
        print(f"Reverting contract {contract_id} elements field to NULL/None")
        
        stmt = update(Contract).where(Contract.contract_id == contract_id).values(elements=None)
        await db.execute(stmt)
        await db.commit()
        
        print(f"Successfully reverted contract {contract_id}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(cleanup_test_data())
