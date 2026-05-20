#!/usr/bin/env python3
"""
Verify property enrichment with Bufdir data.
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

async def verify_enrichment():
    print("📊 Verifying Property Enrichment")
    print("=" * 60)
    
    async with SessionLocal() as db:
        # Find properties with Bufdir data in external_data
        result = await db.execute(select(Property).where(Property.external_data.is_not(None)))
        props = result.scalars().all()
        
        enriched = [p for p in props if p.external_data and 'bufdir_institution' in p.external_data]
        print(f"Total enriched properties: {len(enriched)}")
        
        if enriched:
            print(f"\nSample Property: {enriched[0].name}")
            print(f"Address: {enriched[0].address}")
            print("\nBufdir Data Sample:")
            data = enriched[0].external_data['bufdir_institution']
            
            for k, v in data.items():
                if k == 'description':
                    if v:
                        print(f"  {k}: {v[:100]}...")
                    else:
                        print(f"  {k}: None")
                elif k == 'legal_bases':
                    print(f"  {k}: {len(v) if v else 0} legal bases")
                else:
                    print(f"  {k}: {v}")

            # Check coverage
            print(f"\nCoverage:")
            has_image = sum(1 for p in enriched if p.external_data['bufdir_institution'].get('image_url'))
            has_desc = sum(1 for p in enriched if p.external_data['bufdir_institution'].get('description'))
            
            print(f"  Images: {has_image}/{len(enriched)}")
            print(f"  Descriptions: {has_desc}/{len(enriched)}")
        else:
            print("❌ No enriched properties found!")

if __name__ == "__main__":
    asyncio.run(verify_enrichment())
