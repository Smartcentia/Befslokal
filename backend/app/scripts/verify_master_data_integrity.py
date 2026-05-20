import asyncio
import sys
import os
from sqlalchemy import select, func, text
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.getcwd())
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from backend.app.db.session import SessionLocal
from backend.app.domains.core.models.contract import Contract
from backend.app.domains.core.models.unit import Unit
from backend.app.domains.core.models.property import Property
from backend.app.domains.core.models.party import Party
# Import HMS models to resolve helper relationships
from backend.app.domains.hms.models.risk import RiskAssessment
from backend.app.domains.hms.models.internal_control import InternalControlCase
from backend.app.domains.core.models.user import User

async def verify_integrity():
    async with SessionLocal() as session:
        print("--- MASTER DATA INTEGRITY CHECK ---")
        
        # 1. Check Property Enrichment
        # Count properties with non-null master_data in external_data
        stmt = select(func.count(Property.property_id)).where(Property.external_data['master_data'].isnot(None))
        result = await session.execute(stmt)
        enriched_count = result.scalar()
        print(f"[CHECK 1] Properties Enriched with Master Data: {enriched_count}")
        if enriched_count == 0:
            print("[FAIL] No properties have master data!")
        else:
            print("[PASS] Enriched properties found.")

        # 2. Check Specific Fields on a Sample
        stmt = select(Property).where(Property.external_data['master_data'].isnot(None)).limit(1)
        result = await session.execute(stmt)
        prop = result.scalars().first()
        
        if prop:
            md = prop.external_data.get('master_data', {})
            fin = prop.external_data.get('financials', {})
            print(f"\n[CHECK 2] Sample Property: {prop.address}")
            print(f"  - Title Holder: {md.get('title_holder')}")
            print(f"  - Archive Name: {md.get('archive_name')}")
            print(f"  - Approved Places: {prop.approved_places}")
            print(f"  - Municipal Fees: {fin.get('municipal_fees')}")
            
            if md.get('title_holder') or prop.approved_places is not None:
                print("[PASS] Specific fields populated.")
            else:
                print("[WARN] Some specific fields might be missing on this sample.")
        else:
             print("[FAIL] Could not fetch sample property.")

        # 3. Check Unit Hierarchy (MasterImportDefault)
        stmt = select(func.count(Unit.unit_id)).where(Unit.purpose == 'MasterImportDefault')
        result = await session.execute(stmt)
        unit_count = result.scalar()
        print(f"\n[CHECK 3] Default Units Created: {unit_count}")
        
        if unit_count > 0:
             print("[PASS] Default units exist for contract linking.")
        else:
             print("[WARN] No default units found. Contracts might be unlinked if they relied on this.")

        # 4. Check Contract Linkage
        # Find a contract linked to a MasterImportDefault unit
        stmt = select(Contract).join(Unit).where(Unit.purpose == 'MasterImportDefault').limit(1)
        result = await session.execute(stmt)
        contract = result.scalars().first()
        
        if contract:
            print(f"\n[CHECK 4] Sample Linked Contract: {contract.contract_id}")
            print(f"  - Linked Unit ID: {contract.unit_id}")
            print(f"  - Status: {contract.status}")
            print("[PASS] Contracts are successfully linked to the new unit hierarchy.")
        else:
            print("\n[CHECK 4] No contracts found linked to Default Units (might be okay if all had existing units, but verify).")

        print("\n--- CHECK COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(verify_integrity())
