
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party
from app.domains.core.models.unit import Unit

# Import all models to ensure SQLAlchemy relationships are registered
# (This is required because of circular dependencies in relationships)
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

async def verify_data():
    async with SessionLocal() as db:
        print("\n🔍 VERIFYING IMPORTED DATA")
        print("="*60)

        # 1. Check Properties Enrichment
        print("\nChecking Property Enrichment (Sample of 5 with region):")
        stmt = select(Property).where(Property.region.isnot(None)).limit(5)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        for p in properties:
            print(f"- {p.address} ({p.postal_code} {p.city})")
            print(f"  Region: {p.region}, Municipality: {p.municipality}")
            print(f"  Area: {p.total_area} m2, Gnr/Bnr: {p.gnr}/{p.bnr}")
            print("-" * 40)

        # 2. Check Contracts
        print("\nChecking Contracts (Sample of 5 active):")
        stmt = select(Contract).options(
            joinedload(Contract.unit).joinedload(Unit.property),
            joinedload(Contract.party)
        ).where(Contract.status == 'active').limit(5)
        result = await db.execute(stmt)
        contracts = result.scalars().all()

        for c in contracts:
            prop_addr = c.unit.property.address if c.unit and c.unit.property else "Unknown Property"
            landlord = c.party.name if c.party else "Unknown Landlord"
            amount = c.amount.get('amount_per_year') if c.amount else 0
            print(f"- Contract at {prop_addr}")
            print(f"  Landlord: {landlord}")
            print(f"  Duration: {c.start_date} -> {c.end_date}")
            print(f"  Annual Rent: {amount} NOK")
            print("-" * 40)

        # 3. Stats
        count_props = await db.scalar(select(func.count(Property.property_id)))
        count_contracts = await db.scalar(select(func.count(Contract.contract_id)))
        count_parties = await db.scalar(select(func.count(Party.party_id)))
        
        print("\n📊 Summary Stats:")
        print(f"Total Properties: {count_props}")
        print(f"Total Contracts:  {count_contracts}")
        print(f"Total Parties:    {count_parties}")

if __name__ == "__main__":
    asyncio.run(verify_data())
