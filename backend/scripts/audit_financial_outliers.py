#!/usr/bin/env python3
"""
Comprehensive audit to find financial data outliers and suspicious values
"""

import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from decimal import Decimal

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit


def safe_float(value, default=0.0):
    """Safely convert value to float"""
    if value is None:
        return default
    try:
        if isinstance(value, (int, float, Decimal)):
            return float(value)
        if isinstance(value, str):
            # Remove whitespace and commas
            value = value.strip().replace(',', '').replace(' ', '')
            if value == '':
                return default
            return float(value)
        return default
    except (ValueError, TypeError):
        return default


async def audit_financial_outliers():
    print("=" * 100)
    print("COMPREHENSIVE FINANCIAL DATA OUTLIERS AUDIT")
    print("=" * 100)
    
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
        
        # Collect all financial data for analysis
        all_data = []
        
        for prop in properties:
            prop_id = prop.property_id
            ext = prop.external_data or {}
            financials = ext.get('financials', {})
            
            # Extract rent from contracts
            total_rent = 0
            contract_count = 0
            for contract in contracts:
                if contract.unit and contract.unit.property and contract.unit.property.property_id == prop_id:
                    contract_count += 1
                    amount_data = contract.amount if isinstance(contract.amount, dict) else {}
                    rent = safe_float(amount_data.get('amount_per_year', 0))
                    total_rent += rent
            
            # Extract manual expenses
            manual_expenses = financials.get('manual_expenses', [])
            total_manual = safe_float(financials.get('total_manual_expenses', 0))
            
            # Extract CSV expenses
            total_csv = safe_float(financials.get('total_spend_csv', 0))
            
            # Individual expense categories from different sources
            other_costs = {}
            for key in ['energi_kost', 'renhold_kost', 'kortleser_kost', 'renovasjon_kost', 
                       'forsikring_kost', 'vedlikehold_kost', 'eiendom_skatt', 'feie_kost']:
                value = safe_float(financials.get(key, 0))
                if value > 0:
                    other_costs[key] = value
            
            # Calculate individual expense total
            manual_calculated = sum(safe_float(exp.get('amount', 0)) for exp in manual_expenses)
            
            # Calculate total costs
            total_costs = total_manual + total_csv + sum(other_costs.values())
            
            entry = {
                'property_id': prop_id,
                'name': prop.name,
                'region': prop.region or 'Unknown',
                'address': prop.address or '',
                'total_rent': total_rent,
                'contract_count': contract_count,
                'total_manual': total_manual,
                'total_csv': total_csv,
                'manual_expenses_count': len(manual_expenses),
                'manual_calculated': manual_calculated,
                'other_costs': other_costs,
                'other_costs_sum': sum(other_costs.values()),
                'total_costs': total_costs,
            }
            
            all_data.append(entry)
        
        # Now detect outliers and anomalies
        print("\n" + "=" * 100)
        print("ANOMALY DETECTION")
        print("=" * 100)
        
        # 1. Check for extremely large values (likely errors)
        suspicious_large_costs = []
        suspicious_large_rent = []
        
        COST_THRESHOLD = 50_000_000  # 50M kr seems unreasonable for annual property costs
        RENT_THRESHOLD = 50_000_000  # 50M kr seems unreasonable for annual rent
        
        for entry in all_data:
            if entry['total_costs'] > COST_THRESHOLD:
                suspicious_large_costs.append(entry)
            if entry['total_rent'] > RENT_THRESHOLD:
                suspicious_large_rent.append(entry)
        
        print(f"\n🚨 1. SUSPICIOUSLY LARGE COST VALUES (>{COST_THRESHOLD:,} kr):")
        print(f"   Found {len(suspicious_large_costs)} properties")
        
        if suspicious_large_costs:
            for entry in sorted(suspicious_large_costs, key=lambda x: -x['total_costs']):
                print(f"\n   Property: {entry['name']}")
                print(f"   Region: {entry['region']}")
                print(f"   Total costs: {entry['total_costs']:,.2f} kr ⚠️")
                print(f"     - Manual expenses: {entry['total_manual']:,.2f} kr ({entry['manual_expenses_count']} items)")
                print(f"     - CSV expenses: {entry['total_csv']:,.2f} kr")
                print(f"     - Other costs: {entry['other_costs_sum']:,.2f} kr")
                if entry['other_costs']:
                    for key, val in entry['other_costs'].items():
                        print(f"       • {key}: {val:,.2f} kr")
        
        print(f"\n🚨 2. SUSPICIOUSLY LARGE RENT VALUES (>{RENT_THRESHOLD:,} kr):")
        print(f"   Found {len(suspicious_large_rent)} properties")
        
        if suspicious_large_rent:
            for entry in sorted(suspicious_large_rent, key=lambda x: -x['total_rent']):
                print(f"\n   Property: {entry['name']}")
                print(f"   Region: {entry['region']}")
                print(f"   Total rent: {entry['total_rent']:,.2f} kr ⚠️")
                print(f"   Number of contracts: {entry['contract_count']}")
        
        # 2. Check for mismatched totals (total_manual_expenses != sum of manual_expenses)
        mismatched_totals = []
        MISMATCH_TOLERANCE = 1.0  # Allow 1 kr difference due to rounding
        
        for entry in all_data:
            if entry['manual_expenses_count'] > 0:
                diff = abs(entry['total_manual'] - entry['manual_calculated'])
                if diff > MISMATCH_TOLERANCE:
                    entry['mismatch_amount'] = diff
                    mismatched_totals.append(entry)
        
        print(f"\n🔧 3. MISMATCHED EXPENSE TOTALS:")
        print(f"   Found {len(mismatched_totals)} properties with calculation discrepancies")
        
        if mismatched_totals:
            for entry in sorted(mismatched_totals, key=lambda x: -x['mismatch_amount'])[:20]:
                print(f"\n   Property: {entry['name']}")
                print(f"   Stored total_manual_expenses: {entry['total_manual']:,.2f} kr")
                print(f"   Calculated from expenses: {entry['manual_calculated']:,.2f} kr")
                print(f"   Difference: {entry['mismatch_amount']:,.2f} kr ⚠️")
        
        # 3. Check for unusual ratios (costs/rent)
        unusual_ratios = []
        
        for entry in all_data:
            if entry['total_rent'] > 100_000 and entry['total_costs'] > 100_000:  # Only for properties with meaningful data
                ratio = entry['total_costs'] / entry['total_rent']
                if ratio > 5.0:  # Costs more than 5x rent is unusual
                    entry['cost_to_rent_ratio'] = ratio
                    unusual_ratios.append(entry) 
        
        print(f"\n📊 4. UNUSUAL COST-TO-RENT RATIOS (>5.0):")
        print(f"   Found {len(unusual_ratios)} properties")
        
        if unusual_ratios:
            for entry in sorted(unusual_ratios, key=lambda x: -x['cost_to_rent_ratio'])[:15]:
                print(f"\n   Property: {entry['name']}")
                print(f"   Rent: {entry['total_rent']:,.0f} kr")
                print(f"   Costs: {entry['total_costs']:,.0f} kr")
                print(f"   Ratio: {entry['cost_to_rent_ratio']:.1f}x ⚠️")
        
        # 4. Check for properties with data but zero totals
        zero_totals = []
        
        for entry in all_data:
            if entry['manual_expenses_count'] > 0 and entry['total_manual'] == 0:
                zero_totals.append(entry)
        
        print(f"\n⚠️  5. PROPERTIES WITH EXPENSES BUT ZERO TOTAL:")
        print(f"   Found {len(zero_totals)} properties")
        
        if zero_totals:
            for entry in zero_totals[:15]:
                print(f"   - {entry['name']}: {entry['manual_expenses_count']} expense items but total_manual_expenses = 0")
        
        # Summary
        print("\n" + "=" * 100)
        print("SUMMARY")
        print("=" * 100)
        print(f"Total properties analyzed: {len(all_data)}")
        print(f"Suspicious large costs: {len(suspicious_large_costs)}")
        print(f"Suspicious large rent: {len(suspicious_large_rent)}")
        print(f"Mismatched totals: {len(mismatched_totals)}")
        print(f"Unusual cost/rent ratios: {len(unusual_ratios)}")
        print(f"Zero totals with data: {len(zero_totals)}")
        
        total_issues = len(suspicious_large_costs) + len(suspicious_large_rent) + len(mismatched_totals) + len(unusual_ratios) + len(zero_totals)
        print(f"\n🎯 Total issues requiring review: {total_issues}")
        
        # Export detailed lists
        print(f"\n📝 Exporting detailed lists...")
        
        export_dir = os.path.join(os.path.dirname(__file__), '..')
        
        with open(os.path.join(export_dir, 'financial_outliers_report.txt'), 'w', encoding='utf-8') as f:
            f.write("FINANCIAL DATA OUTLIERS AUDIT REPORT\n")
            f.write("=" * 100 + "\n\n")
            f.write(f"Generated: {__import__('datetime').datetime.now().isoformat()}\n\n")
            
            f.write(f"SUSPICIOUSLY LARGE COSTS (>{COST_THRESHOLD:,} kr):\n")
            f.write("-" * 100 + "\n")
            for entry in sorted(suspicious_large_costs, key=lambda x: -x['total_costs']):
                f.write(f"\nProperty: {entry['name']}\n")
                f.write(f"Region: {entry['region']}\n")
                f.write(f"Address: {entry['address']}\n")
                f.write(f"Total costs: {entry['total_costs']:,.2f} kr\n")
                f.write(f"  - Manual: {entry['total_manual']:,.2f} kr ({entry['manual_expenses_count']} items)\n")
                f.write(f"  - CSV: {entry['total_csv']:,.2f} kr\n")
                f.write(f"  - Other: {entry['other_costs_sum']:,.2f} kr\n")
            
            f.write(f"\n\nSUSPICIOUSLY LARGE RENT (>{RENT_THRESHOLD:,} kr):\n")
            f.write("-" * 100 + "\n")
            for entry in sorted(suspicious_large_rent, key=lambda x: -x['total_rent']):
                f.write(f"\nProperty: {entry['name']}\n")
                f.write(f"Region: {entry['region']}\n")
                f.write(f"Total rent: {entry['total_rent']:,.2f} kr\n")
                f.write(f"Contracts: {entry['contract_count']}\n")
            
            f.write(f"\n\nMISMATCHED EXPENSE TOTALS:\n")
            f.write("-" * 100 + "\n")
            for entry in sorted(mismatched_totals, key=lambda x: -x['mismatch_amount']):
                f.write(f"\nProperty: {entry['name']}\n")
                f.write(f"Stored total: {entry['total_manual']:,.2f} kr\n")
                f.write(f"Calculated: {entry['manual_calculated']:,.2f} kr\n")
                f.write(f"Difference: {entry['mismatch_amount']:,.2f} kr\n")
            
            f.write(f"\n\nUNUSUAL COST-TO-RENT RATIOS (>5.0):\n")
            f.write("-" * 100 + "\n")
            for entry in sorted(unusual_ratios, key=lambda x: -x['cost_to_rent_ratio']):
                f.write(f"\nProperty: {entry['name']}\n")
                f.write(f"Rent: {entry['total_rent']:,.0f} kr\n")
                f.write(f"Costs: {entry['total_costs']:,.0f} kr\n")
                f.write(f"Ratio: {entry['cost_to_rent_ratio']:.1f}x\n")
        
        print(f"   ✅ Exported to: financial_outliers_report.txt")


if __name__ == "__main__":
    asyncio.run(audit_financial_outliers())
