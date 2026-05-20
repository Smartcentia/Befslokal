
import asyncio
import os
import sys
import random
import datetime
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import flag_modified
from copy import deepcopy

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'KNOWME', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'KNOWME', 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.center import Center
from app.domains.core.models.party import Party
from app.domains.core.models.user import User
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control

# Configuration
YEARS_BACK = 6
START_YEAR = 2026 # Generating back from 2025 (current state)
INFLATION_RATE = 0.035 # 3.5% average inflation
RENT_INDEX_ADJ = 0.04 # 4% yearly rent index adjustment

# Seasonal factors for energy (Jan=1.4, Jul=0.6)
SEASONAL_FACTORS = {
    1: 1.4, 2: 1.3, 3: 1.1, 4: 0.9, 5: 0.8, 6: 0.7,
    7: 0.6, 8: 0.7, 9: 0.8, 10: 1.0, 11: 1.2, 12: 1.3
}

async def generate_history():
    print(f"🚀 Starting generation of {YEARS_BACK} years of history...")
    
    async with SessionLocal() as db:
        # 1. Fetch properties with active contracts
        stmt = (
            select(Property)
            .options(joinedload(Property.center)) # Load related if needed
        )
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        updated_count = 0
        
        for prop in properties:
            # Skip if no external data
            if not prop.external_data:
                prop.external_data = {}
            
            ext = prop.external_data
            current_financials = ext.get('financials', {})
            current_expenses = current_financials.get('manual_expenses', [])
            
            # IMPROVED BASE COST LOGIC (Reflects reality better)
            # Use the max of various maintenance/spend fields to find the actual "today" cost
            total_maint = float(current_financials.get('total_maintenance') or 0)
            total_spend_csv = float(current_financials.get('total_spend_csv') or 0)
            total_manual = float(current_financials.get('total_manual_expenses') or 0)
            
            # Base for 2025 consumption (usually 100% of current or slightly less)
            # We apply a scale factor of 2.0 to reach the ~790 MNOK target from the ~396 MNOK raw data
            base_total_costs = max(total_maint, total_spend_csv, total_manual) * 2.0
            
            # Fallback if no spend data
            if base_total_costs == 0:
                # Still use existing logic for properties with NO financial data
                base_total_costs = sum(float(e.get('amount',0)) for e in current_expenses if float(e.get('amount',0)) > 0) * 2.0
            
            # If still 0, we might want a small minimum for synthetic data
            if base_total_costs == 0:
                base_total_costs = random.uniform(50000, 250000) # Small fallback

            # Fetch contracts for base rent
            stmt_contracts = (
                 select(Contract)
                 .join(Unit)
                 .where(Unit.property_id == prop.property_id)
                 .where(Contract.status == 'active')
            )
            res_c = await db.execute(stmt_contracts)
            contracts = res_c.scalars().all()
            
            base_rent = 0.0
            for c in contracts:
                amt = 0
                if c.amount:
                    amt = c.amount.get('amount_per_year') or c.amount.get('total_per_year') or 0
                try: 
                    base_rent += float(amt)
                except: 
                    pass
            
            if base_rent == 0:
                if base_total_costs > 0:
                    base_rent = base_total_costs * 8 

            history = {}
            
            # Generate years 2020-2025
            current_year = 2025
            
            # 2. Loop backwards
            for i in range(YEARS_BACK):
                target_year = current_year - i
                years_diff = i
                
                # A. Rent History
                hist_rent = base_rent / ((1 + RENT_INDEX_ADJ) ** years_diff)
                hist_rent *= random.uniform(0.98, 1.02)
                
                # B. Expense History
                # We use the base_total_costs and distribute it among common categories
                # normalized over years
                
                year_total_base = base_total_costs / ((1 + INFLATION_RATE) ** years_diff)
                
                # Apply special factor for energy crisis years
                if target_year == 2022: year_total_base *= 1.2
                if target_year == 2021: year_total_base *= 1.1
                
                # Distribution of costs
                # 40% Energy, 30% Maintenance, 10% Janitor, 10% Cleaning, 10% Other
                costs_distribution = {
                    "energy": 0.40,
                    "maintenance": 0.30,
                    "janitor": 0.10,
                    "cleaning": 0.10,
                    "other": 0.10
                }
                
                hist_expenses = []
                current_sum = 0
                for cat, share in costs_distribution.items():
                    amt = year_total_base * share * random.uniform(0.85, 1.15)
                    # Spiky maintenance
                    if cat == "maintenance":
                        is_spike = (target_year + int(str(prop.property_id.int)[:2])) % 3 == 0
                        if is_spike: amt *= 1.5
                        else: amt *= 0.7
                    
                    hist_expenses.append({
                        "type": cat,
                        "amount": round(amt, 2),
                        "source": "Syntetisk historikk",
                        "provider": None
                    })
                    current_sum += amt
                
                history[str(target_year)] = {
                    "year": target_year,
                    "rent": round(hist_rent, 2),
                    "total_costs": round(current_sum, 2),
                    "expenses": hist_expenses
                }
            
            # Save to external_data
            ext['financial_history'] = history
            prop.external_data = ext
            flag_modified(prop, "external_data") # Force SQLAlchemy to detect change
            
            updated_count += 1
            if updated_count % 10 == 0:
                print(f"Processed {updated_count} properties...")
        
        await db.commit()
        print(f"✅ Successfully generated history for {updated_count} properties.")

if __name__ == "__main__":
    asyncio.run(generate_history())
