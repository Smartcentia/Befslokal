import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import SessionLocal
from app.domains.core.routers.contracts import get_contract
from app.schemas.contract import Contract
from sqlalchemy import select
from app.domains.core.models.contract import Contract as ContractModel
from app.domains.core.models.unit import Unit as UnitModel
from sqlalchemy.orm import selectinload

async def verify_schema():
    async with SessionLocal() as db:
        # Get a contract ID
        result = await db.execute(select(ContractModel).limit(1))
        contract = result.scalar_one_or_none()
        
        if not contract:
            print("No contracts found in DB to verify.")
            return

        print(f"Verifying Contract ID: {contract.contract_id}")
        
        # Test Eager Loading logic manually since we can't easily call router dependency injected function
        stmt = select(ContractModel).where(ContractModel.contract_id == contract.contract_id).options(
            selectinload(ContractModel.party),
            selectinload(ContractModel.unit).selectinload(UnitModel.property),
            selectinload(ContractModel.files)
        )
        result = await db.execute(stmt)
        contract_loaded = result.scalar_one()
        
        # Serialize with Pydantic
        try:
            contract_pydantic = Contract.model_validate(contract_loaded)
            print("\n--- Pydantic Serialization Successful ---")
            print(contract_pydantic.model_dump_json(indent=2))
            
            # Verify nested fields presence
            data = contract_pydantic.model_dump()
            print("\n--- Checks ---")
            print(f"Unit present: {data.get('unit') is not None}")
            print(f"Party present: {data.get('party') is not None}")
            print(f"Property (root) present: {data.get('property') is not None}")
            print(f"Files list size: {len(data.get('files', []))}")
            
        except Exception as e:
            print(f"\nFATAL: Serialization failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_schema())
