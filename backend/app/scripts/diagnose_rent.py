import asyncio
import os
import sys
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload

# Add backend to path
current_file = os.path.abspath(__file__)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file))) # .../backend
project_root = os.path.dirname(backend_dir) # .../KNOWME

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Load ENV
def get_database_url():
    env_path = os.path.join(backend_dir, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip('"').strip("'")
    return os.environ.get("DATABASE_URL")

os.environ["DATABASE_URL"] = get_database_url()

from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property
from app.domains.core.models.party import Party
from app.domains.core.models.user import User
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase

async def diagnose_rent():
    async with SessionLocal() as db:
        print("Starting Diagnostic...")
        
        # 1. Total Active Contracts
        stmt = select(func.count()).where(Contract.status == 'active')
        total_active_contracts = (await db.execute(stmt)).scalar()
        print(f"Total Active Contracts: {total_active_contracts}")

        # 2. Active Contracts with Linked Property
        stmt = (
            select(func.count())
            .select_from(Contract)
            .join(Unit)
            .where(Contract.status == 'active')
        )
        linked_active_contracts = (await db.execute(stmt)).scalar()
        print(f"Active Contracts linked to Property: {linked_active_contracts}")
        
        # 3. Analyze Rent in Active Contracts
        stmt = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
            .limit(100)  # Check sample
        )
        contracts = (await db.execute(stmt)).scalars().all()
        
        zero_rent_count = 0
        missing_amount_count = 0
        valid_rent_count = 0
        
        print("\nSample Analysis (first 100 active):")
        for c in contracts:
            amount_data = c.amount if isinstance(c.amount, dict) else {}
            rent = amount_data.get('amount_per_year', 0)
            
            try:
                rent_val = float(rent) if rent else 0
            except:
                rent_val = 0
                
            if rent_val > 0:
                valid_rent_count += 1
            elif not amount_data:
                missing_amount_count += 1
                # print(f" - Contract {c.contract_id}: Missing amount data")
            else:
                zero_rent_count += 1
                # print(f" - Contract {c.contract_id}: 0 rent. Raw amount: {c.amount}")
                
        print(f"\nSample Stats:")
        print(f" - Valid Rent: {valid_rent_count}")
        print(f" - Missing Amount Data: {missing_amount_count}")
        print(f" - Zero Rent (but data exists): {zero_rent_count}")

        # 4. Check Properties with 0 Rent
        # Logic matches FinancialAnalysisService
        stmt_prop = select(Property)
        properties = (await db.execute(stmt_prop)).scalars().all()
        
        prop_zero_rent = 0
        prop_with_rent = 0
        
        # Pre-fetch contracts for all properties to simulate service logic
        stmt_all_contracts = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        all_contracts = (await db.execute(stmt_all_contracts)).scalars().all()
        
        prop_contracts = {}
        for c in all_contracts:
            if c.unit and c.unit.property_id:
                pid = c.unit.property_id
                if pid not in prop_contracts:
                    prop_contracts[pid] = []
                prop_contracts[pid].append(c)
                
        for p in properties:
            total_rent = 0
            if p.property_id in prop_contracts:
                for c in prop_contracts[p.property_id]:
                    amount_data = c.amount if isinstance(c.amount, dict) else {}
                    rent = amount_data.get('amount_per_year', 0)
                    try:
                        total_rent += float(rent) if rent else 0
                    except:
                        pass
            
            if total_rent > 0:
                prop_with_rent += 1
            else:
                prop_zero_rent += 1
                contract_count = len(prop_contracts.get(p.property_id, []))
                print(f"Prop 0 Rent: {p.name} (Contracts: {contract_count})")
                
        print(f"\nProperty Stats:")
        print(f" - Properties with Rent > 0: {prop_with_rent}")
        print(f" - Properties with Rent = 0: {prop_zero_rent}")

if __name__ == "__main__":
    asyncio.run(diagnose_rent())
