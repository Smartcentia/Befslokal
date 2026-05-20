
import asyncio
import sys
import os
import json
from sqlalchemy import select
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.user import User
from app.domains.core.models.party import Party

async def audit_sollia():
    async with SessionLocal() as db:
        res = await db.execute(select(Property).where(Property.name.ilike('%Sollia%')))
        props = res.scalars().all()
        
        for p in props:
            print(f"\nProperty: {p.name}")
            print(f"ID: {p.property_id}")
            fin = p.external_data.get('financials', {})
            print(f"Total Manual Cost: {fin.get('total_manual_expenses', 0):,.0f} kr")
            
            # Check for units/contracts
            units_res = await db.execute(select(Unit).where(Unit.property_id == p.property_id))
            units = units_res.scalars().all()
            
            total_income = 0
            for u in units:
                contracts_res = await db.execute(select(Contract).where(Contract.unit_id == u.unit_id))
                contracts = contracts_res.scalars().all()
                for c in contracts:
                    amt = c.amount.get('amount_per_year', 0) if c.amount else 0
                    total_income += amt
            
            print(f"Calculated Annual Income: {total_income:,.0f} kr")

if __name__ == "__main__":
    asyncio.run(audit_sollia())
