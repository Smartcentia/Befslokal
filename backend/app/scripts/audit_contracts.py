
import asyncio
import sys
import os
from sqlalchemy import select
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User
from app.domains.core.models.party import Party

async def audit_contracts():
    async with SessionLocal() as db:
        res = await db.execute(select(Property).where(Property.name.ilike('%Solbakken%')))
        props = res.scalars().all()
        
        for p in props:
            print(f"\nProperty: {p.name} (Address: {p.address})")
            print(f"ID: {p.property_id}")
            
            # Check for units
            units_res = await db.execute(select(Unit).where(Unit.property_id == p.property_id))
            units = units_res.scalars().all()
            print(f"Units found: {len(units)}")
            
            for u in units:
                contracts_res = await db.execute(select(Contract).where(Contract.unit_id == u.unit_id))
                contracts = contracts_res.scalars().all()
                for c in contracts:
                    print(f"  - Contract ID: {c.contract_id}")
                    print(f"    Status: {c.status}")
                    print(f"    External Data: {c.external_data}")
                    if c.amount:
                        print(f"    Amount: {c.amount.get('amount_per_year')} {c.amount.get('currency')}")

if __name__ == "__main__":
    asyncio.run(audit_contracts())
