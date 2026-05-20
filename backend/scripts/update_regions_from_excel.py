#!/usr/bin/env python3
"""
Update 4 property regions from Einovember.xls
"""

import sys
import os
import asyncio
from sqlalchemy import select, update

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property

async def update_regions():
    print("=" * 80)
    print("UPDATING PROPERTY REGIONS FROM EINOVEMBER.XLS")
    print("=" * 80)
    
    # Properties to update
    updates = [
        {'name': 'Ranheim Vestre', 'region': '02 - Midt-Norge'},
        {'name': 'Buvika ungdomssenter', 'region': '02 - Midt-Norge'},
        {'name': 'Humla akuttsenter', 'region': '02 - Midt-Norge'},
        {'name': 'Jong ungdomshjem, hybel i Horniveien', 'region': '05 - Øst'},
    ]
    
    async with SessionLocal() as db:
        updated_count = 0
        not_found = []
        
        for item in updates:
            name = item['name']
            new_region = item['region']
            
            # Find property by name (case-insensitive) - may return multiple
            stmt = select(Property).where(Property.name.ilike(name))
            result = await db.execute(stmt)
            properties = result.scalars().all()
            
            if properties:
                for prop in properties:
                    old_region = prop.region or 'Unknown'
                    
                    # Only update if current region is Unknown or None
                    if not prop.region or str(prop.region).lower() == 'unknown':
                        print(f"\n✅ Updating '{name}' (ID: {prop.property_id})")
                        print(f"   Old region: {old_region}")
                        print(f"   New region: {new_region}")
                        
                        prop.region = new_region
                        updated_count += 1
                    else:
                        print(f"\n⏭️  Skipping '{name}' (ID: {prop.property_id}) - already has region: {prop.region}")
            else:
                not_found.append(name)
                print(f"\n❌ NOT FOUND: '{name}'")
        
        # Commit changes
        if updated_count > 0:
            await db.commit()
            print(f"\n" + "=" * 80)
            print(f"✅ Successfully updated {updated_count} properties")
            
            if not_found:
                print(f"\n⚠️  Could not find {len(not_found)} properties:")
                for name in not_found:
                    print(f"   - {name}")
        else:
            print(f"\n❌ No properties were updated")
        
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(update_regions())
