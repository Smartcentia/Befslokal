#!/usr/bin/env python3
"""
Investigate and fill the 24 remaining properties with 0 rent.
"""
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import flag_modified
from statistics import median

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property

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

# Fallback area for contracts without property area data
DEFAULT_AREA_SQM = 300  # Reasonable default for small properties

async def fill_remaining_zero_rents():
    print("💰 Filling Remaining Zero-Rent Contracts")
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
        
        median_price = median(prices_per_sqm)
        print(f"  Median price: {median_price:,.2f} NOK/m²/year")
        
        # Step 2: Find contracts with 0 rent
        print("\n🔍 Step 2: Finding contracts with 0 rent...")
        
        zero_rent_contracts = []
        
        for c in contracts:
            rent = 0
            if c.amount:
                rent = c.amount.get('amount_per_year') or 0
            
            if rent == 0:
                # Get area
                area = None
                if c.unit and c.unit.property:
                    area = c.unit.property.total_area
                
                # Use default if no area
                if not area or area == 0:
                    area = DEFAULT_AREA_SQM
                
                estimated_rent = area * median_price
                zero_rent_contracts.append({
                    'contract': c,
                    'area': area,
                    'estimated_rent': estimated_rent,
                    'used_default_area': not (c.unit and c.unit.property and c.unit.property.total_area)
                })
        
        print(f"  Found {len(zero_rent_contracts)} contracts with 0 rent")
        
        if not zero_rent_contracts:
            print("\n✅ No contracts with 0 rent!")
            return
        
        # Show breakdown
        with_default = sum(1 for item in zero_rent_contracts if item['used_default_area'])
        print(f"  Using default area ({DEFAULT_AREA_SQM} m²): {with_default}")
        print(f"  Using property area: {len(zero_rent_contracts) - with_default}")
        
        # Step 3: Apply estimates
        print(f"\n💾 Step 3: Applying estimates...")
        
        for item in zero_rent_contracts:
            contract = item['contract']
            
            # Initialize amount dict if needed
            if not contract.amount:
                contract.amount = {}
            
            # Set estimated rent
            contract.amount['amount_per_year'] = item['estimated_rent']
            contract.amount['estimated'] = True
            contract.amount['currency'] = 'NOK'
            if item['used_default_area']:
                contract.amount['used_default_area'] = True
            
            # Mark as modified
            flag_modified(contract, 'amount')
        
        await db.commit()
        
        print(f"\n✅ Successfully estimated {len(zero_rent_contracts)} contract rents!")
        print(f"\n📋 Summary:")
        print(f"  Median price used: {median_price:,.2f} NOK/m²/year")
        print(f"  Default area for missing data: {DEFAULT_AREA_SQM} m²")
        print(f"  Contracts updated: {len(zero_rent_contracts)}")
        
        # Show examples
        print(f"\n📝 Example estimations:")
        for item in zero_rent_contracts[:5]:
            default_flag = " (default area)" if item['used_default_area'] else ""
            print(f"  {item['area']:,.0f} m²{default_flag} × {median_price:,.2f} = {item['estimated_rent']:,.0f} NOK/year")

if __name__ == "__main__":
    asyncio.run(fill_remaining_zero_rents())
