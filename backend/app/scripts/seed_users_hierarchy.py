"""
Lightweight script to seed ONLY the 4-level user hierarchy.
Uses existing properties from database.
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from sqlalchemy import text
from uuid import uuid4
from app.db.session import SessionLocal

# Import all models to ensure relationships are resolved
from app.domains.core.models.user import User, UserRole
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase

async def seed_users_only():
    async with SessionLocal() as db:
        print("=== HMS User Hierarchy Seeding ===\n")
        
        # Get existing properties
        result = await db.execute(text("SELECT property_id, address, city FROM properties ORDER BY city, address"))
        properties = result.fetchall()
        print(f"✅ Found {len(properties)} properties in database\n")
        
        if len(properties) == 0:
            print("⚠️  No properties found! Cannot create caretakers.")
            return
        
        # Level 4: Bufdir (National) - ADMIN
        print("Creating Level 4 (Bufdir - National)...")
        bufdir_email = "admin@bufdir.no"
        exists = await db.execute(text(f"SELECT 1 FROM users WHERE email = '{bufdir_email}'"))
        if not exists.scalar():
            bufdir_admin = User(
                user_id=uuid4(),
                email=bufdir_email,
                name="Bufdir Administrator",
                role=UserRole.ADMIN,
                region=None
            )
            db.add(bufdir_admin)
            print(f"  ✓ {bufdir_email}")
        else:
            print(f"  - {bufdir_email} (already exists)")
        
        await db.commit()
        
        # Level 3: Regional Managers
        print("\nCreating Level 3 (Regional Managers)...")
        regions = ["Region Øst", "Region Vest", "Region Midt", "Region Nord", "Region Sør"]
        regional_count = 0
        
        for region in regions:
            email = f"region.{region.lower().replace(' ', '').replace('ø', 'o')}@bufetat.no"
            exists = await db.execute(text(f"SELECT 1 FROM users WHERE email = '{email}'"))
            if not exists.scalar():
                user = User(
                    user_id=uuid4(),
                    email=email,
                    name=f"Regionsleder {region}",
                    role=UserRole.REGIONAL_MANAGER,
                    region=region
                )
                db.add(user)
                regional_count += 1
                print(f"  ✓ {email}")
            else:
                print(f"  - {email} (already exists)")
        
        await db.commit()
        
        # Level 2: Area Managers
        print("\nCreating Level 2 (Area Managers - Områdeledere)...")
        areas = [
            {"name": "Lillestrøm", "region": "Region Øst"},
            {"name": "Drammen", "region": "Region Øst"},
            {"name": "Stavanger", "region": "Region Vest"},
            {"name": "Trondheim", "region": "Region Midt"},
            {"name": "Tromsø", "region": "Region Nord"},
        ]
        area_count = 0
        
        for area in areas:
            email = f"leder.{area['name'].lower()}@bufetat.no"
            exists = await db.execute(text(f"SELECT 1 FROM users WHERE email = '{email}'"))
            if not exists.scalar():
                user = User(
                    user_id=uuid4(),
                    email=email,
                    name=f"Områdeleder {area['name']}",
                    role=UserRole.PROPERTY_MANAGER,
                    region=area["region"]
                )
                db.add(user)
                area_count += 1
                print(f"  ✓ {email}")
            else:
                print(f"  - {email} (already exists)")
        
        await db.commit()
        
        # Level 1: Property Caretakers (vaktmeste per eiendom)
        print(f"\nCreating Level 1 (Property Caretakers - 1 per eiendom)...")
        print(f"This will create {len(properties)} caretakers...")
        
        caretaker_count = 0
        batch_size = 50
        
        for i, (property_id, address, city) in enumerate(properties):
            # Create clean identifier from address
            clean_addr = address.split()[0].lower()
            clean_addr = clean_addr.replace('ø', 'o').replace('å', 'a').replace('æ', 'ae')
            email = f"vaktmester.{clean_addr}.{i+1}@bufetat.no"
            
            # Check if user exists
            exists = await db.execute(text(f"SELECT 1 FROM users WHERE email = '{email}'"))
            if not exists.scalar():
                # Assign region based on city (simplified)
                region_map = {
                    "OSLO": "Region Øst",
                    "DRAMMEN": "Region Øst",
                    "STAVANGER": "Region Vest",
                    "BERGEN": "Region Vest",
                    "TRONDHEIM": "Region Midt",
                    "TROMSØ": "Region Nord",
                }
                region = region_map.get(city.upper(), "Region Øst")  # Default to Øst
                
                pm = User(
                    user_id=uuid4(),
                    email=email,
                    name=f"Vaktmester {address}",
                    role=UserRole.PROPERTY_MANAGER,
                    region=region
                )
                
                # Link to specific property
                prop_obj = await db.get(Property, property_id)
                if prop_obj:
                    pm.properties.append(prop_obj)
                    db.add(pm)
                    caretaker_count += 1
                    
                    if caretaker_count % 10 == 0:
                        print(f"  ... {caretaker_count} caretakers created")
            
            # Commit in batches to avoid memory issues
            if (i + 1) % batch_size == 0:
                await db.commit()
        
        # Final commit
        await db.commit()
        print(f"  ✓ Created {caretaker_count} new caretakers")
        
        print(f"\n=== Summary ===")
        print(f"Level 4 (Bufdir): 1 admin")
        print(f"Level 3 (Region): {regional_count} regional managers created")
        print(f"Level 2 (Område): {area_count} area managers created")
        print(f"Level 1 (Lokasjon): {caretaker_count} property caretakers created")
        print(f"\n✅ User hierarchy seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_users_only())
