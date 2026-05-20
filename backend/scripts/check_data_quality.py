
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select, func, text, desc
from sqlalchemy.orm import joinedload
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.property import Property
from app.domains.core.models.party import Party
import app.domains.core.models.user
import app.domains.core.models.unit # Register Unit
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control

async def check_quality():
    async with SessionLocal() as db:
        print("\n🔍 DEEP DATA QUALITY CHECK")
        print("="*60)
        
        # 1. Financial Sanity Check
        print("\n💰 Financial Sanity Check")
        result = await db.execute(select(Contract).where(Contract.status == 'active'))
        contracts = result.scalars().all()
        
        zero_rent = 0
        high_rent = 0
        total_rent = 0
        valid_rent_count = 0
        
        high_threshold = 50_000_000 # 50 Million NOK
        
        for c in contracts:
            amt = c.amount.get('amount_per_year') if c.amount else 0
            if amt is None: amt = 0
            
            if amt == 0:
                zero_rent += 1
            elif amt > high_threshold:
                print(f"  ⚠️  Suspiciously high rent: {amt:,.0f} NOK (Contract ID: {c.contract_id})")
                high_rent += 1
            else:
                total_rent += amt
                valid_rent_count += 1
                
        avg_rent = total_rent / valid_rent_count if valid_rent_count else 0
        print(f"  Contracts with 0 NOK rent: {zero_rent}")
        print(f"  Contracts > {high_threshold/1e6}M NOK: {high_rent}")
        print(f"  Average Annual Rent: {avg_rent:,.0f} NOK")

        # 2. Date Validity
        print("\n📅 Date Validity Check")
        invalid_dates = 0
        expired_active = 0
        today = datetime.now().date()
        
        for c in contracts:
            if c.start_date and c.end_date:
                if c.end_date < c.start_date:
                    print(f"  ❌ Invalid range: End ({c.end_date}) < Start ({c.start_date}) [ID: {c.contract_id}]")
                    invalid_dates += 1
                
                # end_date is already a date object, no need to call .date()
                end_date = c.end_date if isinstance(c.end_date, datetime) else c.end_date
                if isinstance(end_date, datetime):
                    end_date = end_date.date()
                if end_date < today and c.status == 'active':
                    # This might be valid if they are just expired but not yet formally terminated in system
                    expired_active += 1
                    
        print(f"  Invalid date ranges: {invalid_dates}")
        print(f"  Expired but status='active': {expired_active}")

        # 3. Missing Critical Fields
        print("\n❓ Completeness Check")
        missing_gnr_bnr = 0
        missing_area = 0
        
        props_result = await db.execute(select(Property).where(Property.region.isnot(None)))
        enriched_props = props_result.scalars().all()
        
        for p in enriched_props:
            if not p.gnr or not p.bnr:
                missing_gnr_bnr += 1
            if not p.total_area:
                missing_area += 1
                
        print(f"  Enriched Properties missing Gnr/Bnr: {missing_gnr_bnr} / {len(enriched_props)}")
        print(f"  Enriched Properties missing Area: {missing_area} / {len(enriched_props)}")

        # 4. Top Landlords
        print("\n👑 Top 5 Landlords by Annual Rent")
        landlord_stats = {}
        
        for c in contracts:
            if not c.party_id: continue
            if not c.amount: continue
            amt = c.amount.get('amount_per_year', 0) or 0
            
            landlord_stats[c.party_id] = landlord_stats.get(c.party_id, 0) + amt
            
        # Get names
        ids = list(landlord_stats.keys())
        if ids:
            parties_res = await db.execute(select(Party).where(Party.party_id.in_(ids)))
            parties = {p.party_id: p.name for p in parties_res.scalars().all()}
            
            sorted_landlords = sorted(landlord_stats.items(), key=lambda x: x[1], reverse=True)[:5]
            
            for pid, total in sorted_landlords:
                name = parties.get(pid, "Unknown")
                print(f"  - {name}: {total:,.0f} NOK/year")

if __name__ == "__main__":
    asyncio.run(check_quality())
