
import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv()

from app.db.session import SessionLocal
from app.domains.hms.models.internal_control import InternalControlCase
from app.schemas.internal_control import InternalControlCase as CaseSchema
from sqlalchemy import select

async def verify_cases():
    print("Verifying Cases Serialization...")
    async with SessionLocal() as db:
        result = await db.execute(select(InternalControlCase))
        cases = result.scalars().all()
        
        if not cases:
            print("No cases found in DB.")
            return

        print(f"Found {len(cases)} cases.")
        first_case = cases[0]
        
        # Verify ORM relationship
        print(f"Case Title: {first_case.title}")
        try:
            print(f"Property Address (ORM): {first_case.property.address}")
        except Exception as e:
            print(f"Failed to access property via ORM: {e}")

        # Verify Pydantic Serialization
        try:
            pydantic_case = CaseSchema.model_validate(first_case)
            print("Pydantic Validation Success!")
            print(f"Property in Pydantic: {pydantic_case.property}")
            if pydantic_case.property and pydantic_case.property.address:
                 print("SUCCESS: Property details are present in schema.")
            else:
                 print("FAILURE: Property details missing in schema.")
        except Exception as e:
            print(f"Pydantic Validation Failed: {e}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(verify_cases())
