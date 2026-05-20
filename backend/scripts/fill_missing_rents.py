#!/usr/bin/env python3
"""
Fill missing rent values using median price per square meter.
"""
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import flag_modified
from statistics import median

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property

# Import all models
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

async def fill_missing_rents():
    print("💰 Filling Missing Rent Values")
    print("=" * 60)
    
    async with SessionLocal() as db:
        # Step 1: Calculate median price per sqm
        print("\n📊 Step 1: Calculating median price per sqm...")
        
        result = await db.execute(
            select(Contract).options(
                joinedload(Contract.unit).joinedload(Unit.property)
            )
        )
        contracts = result.scalars().all()
        
        prices_per_sqm = []
        for c in contracts:
            if not c.amount:
                continue
            rent = c.amount.get('amount_per_year')
            if not rent or rent == 0:
                continue
            
            if not c.unit or not c.unit.property:
                continue
            
            area = c.unit.property.total_area
            if not area or area == 0:
                continue
            
            prices_per_sqm.append(rent / area)
        
        if not prices_per_sqm:
            print("❌ No valid price data found!")
            return
        
        median_price = median(prices_per_sqm)
        print(f"  Median price: {median_price:,.2f} NOK/m²/year")
        print(f"  Based on {len(prices_per_sqm)} contracts")
        
        # Step 2: Find contracts needing estimation
        print("\n🔍 Step 2: Finding contracts with missing rent...")
        
        to_estimate = []
        no_area = []
        
        for c in contracts:
            # Check if rent is missing
            rent = 0
            if c.amount:
                rent = c.amount.get('amount_per_year') or 0
            
            if rent == 0:
                # Check if area is available
                if c.unit and c.unit.property and c.unit.property.total_area:
                    area = c.unit.property.total_area
                    estimated_rent = area * median_price
                    to_estimate.append({
                        'contract': c,
                        'area': area,
                        'estimated_rent': estimated_rent
                    })
                else:
                    no_area.append(c.contract_id)
        
        print(f"  Can estimate: {len(to_estimate)} contracts")
        print(f"  No area data: {len(no_area)} contracts (will remain NULL)")
        
        if not to_estimate:
            print("\n✅ No contracts need estimation!")
            return
        
        # Step 3: Apply estimates
        print(f"\n💾 Step 3: Applying estimates to {len(to_estimate)} contracts...")
        
        for item in to_estimate:
            contract = item['contract']
            
            # Initialize amount dict if needed
            if not contract.amount:
                contract.amount = {}
            
            # Set estimated rent
            contract.amount['amount_per_year'] = item['estimated_rent']
            contract.amount['estimated'] = True
            contract.amount['currency'] = 'NOK'
            
            # Mark as modified for SQLAlchemy
            flag_modified(contract, 'amount')
        
        # Commit changes
        await db.commit()
        
        print(f"\n✅ Successfully estimated {len(to_estimate)} contract rents!")
        print(f"\n📋 Summary:")
        print(f"  Median price used: {median_price:,.2f} NOK/m²/year")
        print(f"  Contracts updated: {len(to_estimate)}")
        print(f"  Contracts with no area: {len(no_area)}")
        
        # Show some examples
        print(f"\n📝 Example estimations:")
        for item in to_estimate[:5]:
            print(f"  {item['area']:,.0f} m² × {median_price:,.2f} = {item['estimated_rent']:,.0f} NOK/year")

if __name__ == "__main__":
    asyncio.run(fill_missing_rents())
