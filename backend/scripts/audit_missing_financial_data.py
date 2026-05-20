#!/usr/bin/env python3
"""
Comprehensive audit to find properties missing financial data
"""

import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit

async def audit_missing_financial_data():
    print("=" * 80)
    print("COMPREHENSIVE FINANCIAL DATA AUDIT")
    print("=" * 80)
    
    async with SessionLocal() as db:
        # Get all properties
        stmt_prop = select(Property)
        result_prop = await db.execute(stmt_prop)
        properties = result_prop.scalars().all()
        
        # Get all active contracts with property info
        stmt_contract = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        result_contract = await db.execute(stmt_contract)
        contracts = result_contract.scalars().all()
        
        print(f"\n📊 Database Statistics:")
        print(f"   Total properties: {len(properties)}")
        print(f"   Active contracts: {len(contracts)}")
        
        # Build property -> contract mapping
        property_contracts = {}
        for contract in contracts:
            if contract.unit and contract.unit.property:
                prop_id = contract.unit.property.property_id
                if prop_id not in property_contracts:
                    property_contracts[prop_id] = []
                property_contracts[prop_id].append(contract)
        
        # Categorize properties
        complete_data = []        # Has both rent and costs
        has_rent_only = []        # Has rent but no costs
        has_costs_only = []       # Has costs but no rent
        missing_all = []          # Missing both
        
        for prop in properties:
            prop_id = prop.property_id
            
            # Check for rent data
            has_rent = False
            rent_amount = 0
            if prop_id in property_contracts:
                for contract in property_contracts[prop_id]:
                    amount_data = contract.amount if isinstance(contract.amount, dict) else {}
                    rent = amount_data.get('amount_per_year', 0)
                    try:
                        rent = float(rent) if rent else 0
                    except:
                        rent = 0
                    
                    if rent > 0:
                        has_rent = True
                        rent_amount += rent
                        break  # Found rent
            
            # Check for cost data
            has_costs = False
            cost_amount = 0
            ext = prop.external_data or {}
            expenses = ext.get('financials', {}).get('manual_expenses', [])
            
            if expenses and len(expenses) > 0:
                has_costs = True
                for exp in expenses:
                    try:
                        amount = float(exp.get('amount', 0) or 0)
                        cost_amount += amount
                    except:
                        pass
            
            # Categorize
            entry = {
                'name': prop.name,
                'region': prop.region or 'Unknown',
                'property_id': prop_id,
                'rent': rent_amount,
                'costs': cost_amount,
                'num_expenses': len(expenses)
            }
            
            if has_rent and has_costs:
                complete_data.append(entry)
            elif has_rent and not has_costs:
                has_rent_only.append(entry)
            elif not has_rent and has_costs:
                has_costs_only.append(entry)
            else:
                missing_all.append(entry)
        
        # Print results
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        
        total = len(properties)
        
        print(f"\n1. COMPLETE DATA (rent + costs): {len(complete_data)} ({100*len(complete_data)/total:.1f}%)")
        print(f"   These properties have both rent and running costs")
        
        print(f"\n2. HAS RENT ONLY (missing costs): {len(has_rent_only)} ({100*len(has_rent_only)/total:.1f}%)")
        if has_rent_only:
            print(f"\n   Top 20 by rent amount:")
            sorted_rent = sorted(has_rent_only, key=lambda x: -x['rent'])
            for entry in sorted_rent[:20]:
                print(f"     {entry['name'][:55]:<55} {entry['rent']:>12,.0f} kr/år (Region: {entry['region']})")
        
        print(f"\n3. HAS COSTS ONLY (missing rent): {len(has_costs_only)} ({100*len(has_costs_only)/total:.1f}%)")
        if has_costs_only:
            print(f"\n   Top 20 by cost amount:")
            sorted_costs = sorted(has_costs_only, key=lambda x: -x['costs'])
            for entry in sorted_costs[:20]:
                print(f"     {entry['name'][:55]:<55} {entry['costs']:>12,.0f} kr/år ({entry['num_expenses']} trans, Region: {entry['region']})")
        
        print(f"\n4. MISSING ALL DATA (no rent, no costs): {len(missing_all)} ({100*len(missing_all)/total:.1f}%)")
        if missing_all:
            print(f"\n   All {len(missing_all)} properties:")
            for entry in sorted(missing_all, key=lambda x: x['name']):
                print(f"     - {entry['name']} (Region: {entry['region']})")
        
        # Summary by region
        print(f"\n" + "=" * 80)
        print("REGIONAL BREAKDOWN")
        print("=" * 80)
        
        region_stats = {}
        for prop in properties:
            region = prop.region or 'Unknown'
            if region not in region_stats:
                region_stats[region] = {
                    'total': 0,
                    'complete': 0,
                    'rent_only': 0,
                    'costs_only': 0,
                    'missing': 0
                }
            region_stats[region]['total'] += 1
        
        # Add to stats
        for entry in complete_data:
            region_stats[entry['region']]['complete'] += 1
        for entry in has_rent_only:
            region_stats[entry['region']]['rent_only'] += 1
        for entry in has_costs_only:
            region_stats[entry['region']]['costs_only'] += 1
        for entry in missing_all:
            region_stats[entry['region']]['missing'] += 1
        
        print(f"\n{'Region':<25} {'Total':>8} {'Complete':>10} {'Rent Only':>11} {'Costs Only':>12} {'Missing':>10}")
        print("-" * 85)
        for region in sorted(region_stats.keys()):
            stats = region_stats[region]
            print(f"{region:<25} {stats['total']:>8} {stats['complete']:>10} {stats['rent_only']:>11} {stats['costs_only']:>12} {stats['missing']:>10}")
        
        print(f"\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total properties: {total}")
        print(f"Complete data: {len(complete_data)} ({100*len(complete_data)/total:.1f}%)")
        print(f"Missing rent: {len(has_costs_only) + len(missing_all)} ({100*(len(has_costs_only) + len(missing_all))/total:.1f}%)")
        print(f"Missing costs: {len(has_rent_only) + len(missing_all)} ({100*(len(has_rent_only) + len(missing_all))/total:.1f}%)")
        print(f"Missing everything: {len(missing_all)} ({100*len(missing_all)/total:.1f}%)")
        
        # Export detailed list
        print(f"\n📝 Exporting detailed lists...")
        
        export_dir = os.path.join(os.path.dirname(__file__), '..')
        
        # Export missing all
        with open(os.path.join(export_dir, 'missing_all_financial_data.txt'), 'w', encoding='utf-8') as f:
            f.write("PROPERTIES MISSING ALL FINANCIAL DATA\n")
            f.write("=" * 80 + "\n\n")
            for entry in sorted(missing_all, key=lambda x: x['name']):
                f.write(f"{entry['name']} (Region: {entry['region']})\n")
        
        # Export missing rent
        with open(os.path.join(export_dir, 'missing_rent_data.txt'), 'w', encoding='utf-8') as f:
            f.write("PROPERTIES MISSING RENT DATA\n")
            f.write("=" * 80 + "\n\n")
            all_missing_rent = has_costs_only + missing_all
            for entry in sorted(all_missing_rent, key=lambda x: -x['costs']):
                f.write(f"{entry['name']}\n")
                f.write(f"  Region: {entry['region']}\n")
                f.write(f"  Running costs: {entry['costs']:,.0f} kr/år ({entry['num_expenses']} transactions)\n\n")
        
        # Export missing costs
        with open(os.path.join(export_dir, 'missing_cost_data.txt'), 'w', encoding='utf-8') as f:
            f.write("PROPERTIES MISSING RUNNING COSTS DATA\n")
            f.write("=" * 80 + "\n\n")
            all_missing_costs = has_rent_only + missing_all
            for entry in sorted(all_missing_costs, key=lambda x: -x['rent']):
                f.write(f"{entry['name']}\n")
                f.write(f"  Region: {entry['region']}\n")
                f.write(f"  Rent: {entry['rent']:,.0f} kr/år\n\n")
        
        print(f"   ✅ Exported to backend/ directory:")
        print(f"      - missing_all_financial_data.txt ({len(missing_all)} properties)")
        print(f"      - missing_rent_data.txt ({len(has_costs_only) + len(missing_all)} properties)")
        print(f"      - missing_cost_data.txt ({len(has_rent_only) + len(missing_all)} properties)")

if __name__ == "__main__":
    asyncio.run(audit_missing_financial_data())
