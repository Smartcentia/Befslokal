#!/usr/bin/env python3
"""
Check property names in database.
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

async def check_names():
    print("🏢 Checking Property Names")
    print("=" * 60)
    
    async with SessionLocal() as db:
        result = await db.execute(select(Property))
        props = result.scalars().all()
        
        with_name = sum(1 for p in props if p.name)
        total = len(props)
        print(f"Properties with names: {with_name}/{total}")
        
        # Sample names
        print("\nUsing CSV Avtalenavn if name is missing?")
        
        # Check if we should populate names from CSV
        print("\nSample properties:")
        for p in props[:10]:
            print(f"- {p.address}: {p.name or 'NULL'}")

if __name__ == "__main__":
    asyncio.run(check_names())
