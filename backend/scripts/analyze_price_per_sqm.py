#!/usr/bin/env python3
"""
Analyze contract data to calculate average price per square meter for rent estimation.
"""
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload

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

async def analyze_price_per_sqm():
    print("📊 Analyzing Price per Square Meter")
    print("=" * 60)
    
    async with SessionLocal() as db:
        # Get all contracts with units and properties
        result = await db.execute(
            select(Contract).options(
                joinedload(Contract.unit).joinedload(Unit.property)
            )
        )
        contracts = result.scalars().all()
        
        # Calculate price per sqm for contracts with complete data
        price_per_sqm_data = []
        
        for c in contracts:
            # Get annual rent
            if not c.amount:
                continue
            rent = c.amount.get('amount_per_year')
            if not rent or rent == 0:
                continue
            
            # Get area from property
            if not c.unit or not c.unit.property:
                continue
            
            area = c.unit.property.total_area
            if not area or area == 0:
                continue
            
            price_per_sqm = rent / area
            price_per_sqm_data.append({
                'contract_id': c.contract_id,
                'rent': rent,
                'area': area,
                'price_per_sqm': price_per_sqm
            })
        
        print(f"\nFound {len(price_per_sqm_data)} contracts with complete data (rent + area)")
        
        if not price_per_sqm_data:
            print("❌ No contracts with both rent and area data found!")
            return
        
        # Calculate statistics
        prices = [d['price_per_sqm'] for d in price_per_sqm_data]
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        median_price = sorted(prices)[len(prices) // 2]
        
        print(f"\n📈 Price per Square Meter Statistics:")
        print(f"  Average: {avg_price:,.2f} NOK/m²/year")
        print(f"  Median:  {median_price:,.2f} NOK/m²/year")
        print(f"  Min:     {min_price:,.2f} NOK/m²/year")
        print(f"  Max:     {max_price:,.2f} NOK/m²/year")
        
        # Show distribution
        print(f"\n📊 Distribution:")
        ranges = [
            (0, 1000, "0-1k"),
            (1000, 2000, "1k-2k"),
            (2000, 3000, "2k-3k"),
            (3000, 5000, "3k-5k"),
            (5000, 10000, "5k-10k"),
            (10000, float('inf'), "10k+")
        ]
        
        for min_r, max_r, label in ranges:
            count = len([p for p in prices if min_r <= p < max_r])
            if count > 0:
                pct = (count / len(prices)) * 100
                print(f"  {label:8s}: {count:3d} contracts ({pct:5.1f}%)")
        
        # Count contracts needing estimation
        print(f"\n🔍 Contracts needing rent estimation:")
        missing_rent = 0
        has_area = 0
        
        for c in contracts:
            rent = 0
            if c.amount:
                rent = c.amount.get('amount_per_year') or 0
            
            if rent == 0:
                missing_rent += 1
                if c.unit and c.unit.property and c.unit.property.total_area:
                    has_area += 1
        
        print(f"  Total with 0/NULL rent: {missing_rent}")
        print(f"  Of these, have area data: {has_area}")
        print(f"  Cannot estimate (no area): {missing_rent - has_area}")
        
        return avg_price

if __name__ == "__main__":
    asyncio.run(analyze_price_per_sqm())
