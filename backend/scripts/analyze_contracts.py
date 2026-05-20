
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select, func, text
from sqlalchemy.orm import joinedload
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit

# Import all models to ensure relationships work
import app.domains.core.models.user
import app.domains.core.models.property
import app.domains.core.models.contract
import app.domains.core.models.audit
import app.domains.core.models.unit
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control

async def analyze_data():
    async with SessionLocal() as db:
        print("\n🔍 ANALYZING DATA DUPLICATION & COVERAGE")
        print("="*60)

        # 1. Check for Duplicate Contracts
        # We define a "duplicate" as having the same unit_id, start_date, end_date, and amount
        print("\nChecking for potential duplicate contracts...")
        
        # Fetch all active contracts
        stmt = select(Contract).where(Contract.status == 'active')
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        # Create a signature for each contract
        signatures = []
        for c in contracts:
            amt = c.amount.get('amount_per_year') if c.amount else None
            sig = (c.unit_id, c.start_date, c.end_date, amt)
            signatures.append(sig)
            
        counts = Counter(signatures)
        duplicates = {k: v for k, v in counts.items() if v > 1}
        
        print(f"Total Active Contracts: {len(contracts)}")
        print(f"Unique Signatures: {len(counts)}")
        print(f"Potential Duplicates: {sum(v-1 for v in duplicates.values())}")
        
        if duplicates:
            print("\nExample Duplicates:")
            count = 0
            for sig, num in duplicates.items():
                if count >= 5: break
                unit_id, start, end, amt = sig
                print(f"- Found {num} copies of contract: Unit {unit_id}, {start}->{end}, {amt} NOK")
                count += 1
                
        # 2. Property Coverage
        print("\n\nChecking Property Coverage...")
        
        # Count contracts per property
        stmt = select(
            Property.address, 
            func.count(Contract.contract_id).label('count')
        ).join(Unit, Unit.property_id == Property.property_id)\
         .join(Contract, Contract.unit_id == Unit.unit_id)\
         .group_by(Property.property_id, Property.address)\
         .order_by(text('count DESC'))
         
        result = await db.execute(stmt)
        props_with_contracts = result.all()
        
        print(f"Properties with at least one contract: {len(props_with_contracts)}")
        
        print("\nTop 5 Properties by Contract Count:")
        for row in props_with_contracts[:5]:
            print(f"- {row.address}: {row.count} contracts")

        # 3. Properties WITHOUT contracts
        print("\n\nChecking Orphaned Properties (Enriched but no contracts?)...")
        # Get all properties with region (enriched)
        enriched_props = await db.execute(select(Property).where(Property.region.isnot(None)))
        enriched_props = enriched_props.scalars().all()
        enriched_ids = {p.property_id for p in enriched_props}
        
        # Get ids of properties with contracts
        prop_ids_with_contracts = {p.property_id for p in (await db.execute(select(Property).join(Unit).join(Contract))).scalars().all()}
        
        missing_ids = enriched_ids - prop_ids_with_contracts
        print(f"Enriched properties without contracts: {len(missing_ids)}")
        
        if missing_ids:
            missing_props = [p for p in enriched_props if p.property_id in missing_ids]
            print("Examples:")
            for p in missing_props[:5]:
                print(f"- {p.address}")

if __name__ == "__main__":
    asyncio.run(analyze_data())
