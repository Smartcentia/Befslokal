#!/usr/bin/env python3
"""
Manually update the 3 remaining NULL properties based on CSV findings.
"""
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property

import app.domains.core.models.user
import app.domains.core.models.property
import app.domains.core.models.contract
import app.domains.core.models.audit
import app.domains.core.models.unit
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control
import app.models.file_meta

# Manual mapping based on CSV investigation
# Note: Thorøyaveien 1 is "Thorøya Vaktmesterbolig" - still a Barnevernsinstitusjon facility
MANUAL_UPDATES = {
    'Thorøyaveien 1': 'Barnevernsinstitusjon',  # CSV: Formålsbygg (vaktmesterbolig for Thorøya institusjon)
}

async def update_remaining_nulls():
    print("🔧 Manually Updating Remaining NULL Properties")
    print("=" * 60)
    
    async with SessionLocal() as db:
        updated = 0
        
        for address, usage_type in MANUAL_UPDATES.items():
            result = await db.execute(
                select(Property).where(Property.address == address)
            )
            prop = result.scalar_one_or_none()
            
            if prop:
                old_usage = prop.usage
                prop.usage = usage_type
                updated += 1
                print(f"✓ {address}")
                print(f"  {old_usage or 'NULL'} → {usage_type}")
            else:
                print(f"⚠️  Not found: {address}")
        
        await db.commit()
        
        print(f"\n✅ Updated {updated} properties")
        
        # Verify final state
        print(f"\n📊 Final usage distribution:")
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        
        usage_counts = {}
        for p in properties:
            usage = p.usage or "NULL"
            usage_counts[usage] = usage_counts.get(usage, 0) + 1
        
        for usage, count in sorted(usage_counts.items(), key=lambda x: -x[1]):
            print(f"  {usage}: {count}")

if __name__ == "__main__":
    asyncio.run(update_remaining_nulls())
