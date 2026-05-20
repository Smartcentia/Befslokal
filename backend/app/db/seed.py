import asyncio
import sys
import os
import random
from datetime import datetime, timedelta
import hashlib
from uuid import UUID, uuid4

# Adds backend directory to python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from sqlalchemy import text
from app.db.session import SessionLocal

# Domain Models
from app.domains.core.models.user import User, UserRole
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase

async def seed_data():
    # Ensure tables exist
    from app.db.session import engine
    from app.db.base_class import Base
    # import app.models.user # Removed
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        print("Seeding database...")
        
        # 1. Get existing properties from database
        print("Fetching existing properties from database...")
        result = await db.execute(text("SELECT property_id FROM properties ORDER BY created_at"))
        existing_property_ids = [row[0] for row in result.fetchall()]
        
        print(f"✅ Found {len(existing_property_ids)} existing properties in database")
        
        if len(existing_property_ids) == 0:
            print("⚠️  No properties found! Run property import scripts first.")
            return
        
        # 2. Seed Units (One per property for simplicity)
        print("Seeding units...")
        unit_ids = []
        for pid in existing_property_ids:
            # Check if unit exists
            unit_res = await db.execute(text(f"SELECT unit_id FROM units WHERE property_id = '{pid}'"))
            uid = unit_res.scalar()
            
            if not uid:
                uid = uuid4()
                unit = Unit(
                    unit_id=uid,
                    property_id=pid,
                    purpose="Kontorleie" if random.random() > 0.5 else "Bofellesskap",
                    area_sqm=random.randint(50, 500),
                    floor=random.randint(1, 5)
                )
                db.add(unit)
            
            unit_ids.append(uid)
        
        await db.commit()

        # 3. Seed Parties (Tenants)
        print("Seeding parties...")
        party_names = ["Bufetat Region Øst", "Oslo Kommune", "Statsbygg", "Privat Utleie AS", "Boligstiftelsen"]
        party_ids = []
        
        for name in party_names:
            # Check if party exists
            party_res = await db.execute(text(f"SELECT party_id FROM parties WHERE name = '{name}'"))
            pid = party_res.scalar()
            
            if not pid:
                pid = uuid4()
                party = Party(
                    party_id=pid,
                    name=name,
                    orgnr=str(random.randint(900000000, 999999999)),
                    contact_email=f"post@{name.lower().replace(' ', '')}.no",
                    contact_phone=f"auto-{random.randint(1000,9999)}"
                )
                db.add(party)
            
            party_ids.append(pid)
            
        await db.commit()

        # 4. Seed Contracts
        print("Seeding contracts...")
        for uid in unit_ids:
            # 70% chance of having a contract
            if random.random() < 0.7:
                # Check for existing contract
                contract_res = await db.execute(text(f"SELECT 1 FROM contracts WHERE unit_id = '{uid}'"))
                if not contract_res.scalar():
                    status = "active" if random.random() > 0.2 else "terminated"
                    start_date = datetime.now() - timedelta(days=random.randint(100, 1000))
                    
                    contract = Contract(
                        contract_id=uuid4(),
                        unit_id=uid,
                        party_id=random.choice(party_ids),
                        status=status,
                        periods=[{
                            "start_date": start_date.isoformat(),
                            "end_date": (start_date + timedelta(days=365*3)).isoformat(),
                            "index_name": "KPI"
                        }],
                        amount={
                            "currency": "NOK",
                            "amount_per_year": random.randint(100000, 2000000)
                        },
                        signed_at=start_date,
                        terminated_at=datetime.now() if status == "terminated" else None
                    )
                    db.add(contract)
        
        await db.commit()
        
        # 5. Seed Risks (Deviations) - TEMPORARILY DISABLED
        # Database schema missing 'status' column - needs migration
        print("Skipping risk assessments (database schema mismatch)...")
        # for pid in existing_property_ids:
        #     exists = await db.execute(text(f"SELECT 1 FROM risk_assessments WHERE property_id = '{pid}'"))
        #     if not exists.scalar():
        #         risk_type_map = {
        #             "Critical": "Manglende brannsikring i fellesareal",
        #             "High": "Vannlekkasje i kjeller",
        #             "Medium": "Manglende vedlikeholdsplan",
        #             "Low": "Mangler nøkkelkvittering"
        #         }
        #         category = random.choice([" Low", "Medium", "High", "Critical"])
        #         
        #         risk = RiskAssessment(
        #             property_id=pid,
        #             assessment_date=datetime.now() - timedelta(days=random.randint(0, 60)),
        #             methodology="Auto-Seeder",
        #             overall_risk_score=random.uniform(1.0, 5.0),
        #             risk_category=category,
        #             assessed_by="Auto-Seeder",
        #             notes=risk_type_map[category]
        #         )
        #         db.add(risk)
        #         
        # await db.commit()

        # 6. Seed Users - Complete 4-Level Hierarchy
        print("Seeding users with complete hierarchy...")
        from app.domains.core.models.user import User, UserRole
        
        # Level 4: Bufdir (National) - ADMIN
        bufdir_email = "admin@bufdir.no"
        exists = await db.execute(text(f"SELECT 1 FROM users WHERE email = '{bufdir_email}'"))
        if not exists.scalar():
            bufdir_admin = User(
                user_id=uuid4(),
                email=bufdir_email,
                name="Bufdir Administrator",
                role=UserRole.ADMIN,
                region=None  # National level, no specific region
            )
            db.add(bufdir_admin)
            print(f"  ✓ Created Bufdir admin: {bufdir_email}")
        
        await db.commit()
        
        # Level 3: Regional Managers
        regions = ["Region Øst", "Region Vest", "Region Midt", "Region Nord", "Region Sør"]
        regional_managers = []
        
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
                regional_managers.append(user)
                print(f"  ✓ Created regional manager: {email}")
        
        await db.commit()
        
        # Level 2: Area Managers (Områdeledere)
        areas = [
            {"name": "Lillestrøm", "region": "Region Øst"},
            {"name": "Drammen", "region": "Region Øst"},
            {"name": "Stavanger", "region": "Region Vest"},
            {"name": "Trondheim", "region": "Region Midt"},
            {"name": "Tromsø", "region": "Region Nord"},
        ]
        area_managers = []
        
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
                area_managers.append(user)
                print(f"  ✓ Created area manager: {email}")
        
        await db.commit()
        
        # Level 1: Property Caretakers (Vaktmestre/Eiendomsansvarlige)
        property_managers = []
        
        for i, pid in enumerate(existing_property_ids):
            # Get property address for naming
            prop_res = await db.execute(text(f"SELECT address FROM properties WHERE property_id = '{pid}'"))
            address = prop_res.scalar()
            
            if address:
                # Create a clean identifier from address
                clean_name = address.split()[0].lower().replace('ø', 'o').replace('å', 'a').replace('æ', 'ae')
                email = f"vaktmester.{clean_name}.{i+1}@bufetat.no"
                
                exists = await db.execute(text(f"SELECT 1 FROM users WHERE email = '{email}'"))
                if not exists.scalar():
                    pm = User(
                        user_id=uuid4(),
                        email=email,
                        name=f"Vaktmester {address}",
                        role=UserRole.PROPERTY_MANAGER,
                        region="Region Øst"  # Assign based on property location in production
                    )
                    # Link to specific property
                    prop_obj = await db.get(Property, pid)
                    if prop_obj:
                        pm.properties.append(prop_obj)
                        db.add(pm)
                        property_managers.append(pm)
                        print(f"  ✓ Created caretaker: {email} for {address}")
        
        await db.commit()
        
        print(f"\n=== User Hierarchy Seeding Complete ===")
        print(f"Level 4 (Bufdir): 1 admin")
        print(f"Level 3 (Region): {len(regional_managers)} regional managers")
        print(f"Level 2 (Område): {len(area_managers)} area managers")
        print(f"Level 1 (Lokasjon): {len(property_managers)} property caretakers")
        print(f"Total users: {1 + len(regional_managers) + len(area_managers) + len(property_managers)}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed_data())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(seed_data())
