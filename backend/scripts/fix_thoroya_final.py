#!/usr/bin/env python3
"""
Fix the final Thorøyaveien 1 property usage.
"""
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
# Import all models to ensure relationships are set up correctly
import app.domains.core.models.user
from app.domains.core.models.property import Property
import app.domains.core.models.contract
import app.domains.core.models.audit
import app.domains.core.models.unit
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control
import app.models.file_meta

async def fix_thoroya_final():
    print("🔧 Fixing Thorøyaveien 1 Property Usage")
    print("=" * 60)
    
    async with SessionLocal() as db:
        # Check closely for Thorøyaveien 1, handling whitespace
        result = await db.execute(
            select(Property).where(Property.address.ilike('Thorøyaveien 1%'))
        )
        props = result.scalars().all()
        
        print(f"Found {len(props)} properties matching 'Thorøyaveien 1%':")
        
        updated_count = 0
        for prop in props:
            print(f"\n  ID: {prop.property_id}")
            print(f"  Address: '{prop.address}'")
            print(f"  Current Usage: {prop.usage}")
            
            if prop.usage is None:
                prop.usage = 'Barnevernsinstitusjon'
                updated_count += 1
                print(f"  ➜ Updated to: Barnevernsinstitusjon")
        
        if updated_count > 0:
            await db.commit()
            print(f"\n✅ Successfully updated {updated_count} properties.")
        else:
            print("\n⚠️  No properties needed updating (maybe already done?).")
            
        # Final Verification
        print("\n📊 Final Status Check (All Properties with NULL usage):")
        result = await db.execute(
            select(Property).where(Property.usage == None)
        )
        null_props = result.scalars().all()
        if not null_props:
            print("  🎉 ZERO properties have NULL usage! 100% Complete.")
        else:
            print(f"  ⚠️  Still have {len(null_props)} NULL properties:")
            for p in null_props:
                 print(f"     - {p.address}")

if __name__ == "__main__":
    asyncio.run(fix_thoroya_final())
