import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import SessionLocal
from app.models.user import User
from app.models.property import Property
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def verify_data():
    async with SessionLocal() as db:
        print("--- VERIFYING REAL DATA & USER LINKAGE ---")
        
        # 1. Count Total Properties (Real Data)
        result = await db.execute(select(Property))
        props = result.scalars().all()
        print(f"✅ Real Properties in DB: {len(props)}")
        
        if not props:
            print("❌ No properties found! Seeding failed?")
            return

        # 2. Count Total Users (Mock Users)
        result = await db.execute(select(User))
        users = result.scalars().all()
        print(f"✅ Mock Users in DB: {len(users)}")
        
        # 3. Verify Links (Users assigned to Properties)
        # Fetch a few properties and check their managers
        print("\n--- SAMPLE LINKAGE CHECK ---")
        
        # We need to fetch properties with managers loaded
        result = await db.execute(
            select(Property)
            .options(selectinload(Property.managers))
            .limit(5)
        )
        sample_props = result.scalars().all()
        
        for p in sample_props:
            print(f"\nProperty: {p.address} (ID: {str(p.property_id)[:8]}...)")
            if p.managers:
                for m in p.managers:
                    print(f"   -> Managed by: {m.name} ({m.email}) [{m.role}]")
            else:
                print("   -> ⚠️ No Manager Assigned!")
                
        # 4. Verify Regional Managers
        print("\n--- REGIONAL MANAGERS ---")
        result = await db.execute(select(User).where(User.role == 'REGIONAL_MANAGER'))
        regional_managers = result.scalars().all()
        for rm in regional_managers:
            print(f"Region: {rm.region} - Manager: {rm.name}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(verify_data())
