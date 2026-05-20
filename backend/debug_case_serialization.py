import asyncio
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.domains.core.models.user import User
from app.domains.core.models.center import Center 
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.services.internal_control_service import InternalControlService
from app.schemas.internal_control import InternalControlCase as CaseSchema

async def debug_serialization():
    async with SessionLocal() as db:
        print("Fetching cases...")
        cases = await InternalControlService.get_property_cases(db)
        
        if not cases:
            print("No cases found.")
            return

        print(f"Found {len(cases)} cases. Validating all...")
        
        failed_count = 0
        for i, case in enumerate(cases):
            try:
                # Pydantic v2 validation
                CaseSchema.model_validate(case)
                # print(f"✅ Case {i} OK")
            except Exception as e:
                print(f"❌ Case {i} Serialization Failed: {e}")
                print(f"   Case ID: {case.case_id}")
                print(f"   Property ID: {case.property_id}")
                # print(f"   Data: {case.__dict__}")
                failed_count += 1
        
        if failed_count == 0:
            print("🎉 All cases validated successfully!")
        else:
            print(f"💀 {failed_count} cases failed validation.")

if __name__ == "__main__":
    asyncio.run(debug_serialization())
