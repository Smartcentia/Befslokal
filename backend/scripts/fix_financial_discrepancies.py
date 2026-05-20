#!/usr/bin/env python3
"""
Fix financial data discrepancies with multiple repair strategies
"""

import sys
import os
import asyncio
import argparse
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property


def safe_float(value, default=0.0):
    """Safely convert value to float"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


async def fix_financial_discrepancies(dry_run=True):
    print("=" * 100)
    print("FINANCIAL DATA DISCREPANCY FIX")
    print("=" * 100)
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'APPLY FIXES (changes will be saved)'}")
    print("=" * 100)
    
    async with SessionLocal() as db:
        stmt = select(Property)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        stats = {
            'duplicates_removed': 0,
            'totals_recalculated': 0,
            'zero_totals_fixed': 0,
            'properties_modified': 0
        }
        
        modified_properties = []
        
        for prop in properties:
            ext = prop.external_data or {}
            financials = ext.get('financials', {})
            expenses = financials.get('manual_expenses', [])
            
            if not expenses:
                continue
            
            original_count = len(expenses)
            original_total = safe_float(financials.get('total_manual_expenses', 0))
            modified = False
            
            # Strategy 1: Remove duplicates
            seen_signatures = set()
            unique_expenses = []
            duplicates_found = 0
            
            for exp in expenses:
                # Create signature
                sig = (
                    exp.get('date', ''),
                    exp.get('type', ''),
                    safe_float(exp.get('amount', 0)),
                    exp.get('provider', ''),
                    exp.get('source', '')
                )
                
                if sig not in seen_signatures:
                    seen_signatures.add(sig)
                    unique_expenses.append(exp)
                else:
                    duplicates_found += 1
            
            if duplicates_found > 0:
                print(f"\n📝 Property: {prop.name}")
                print(f"   Duplicates found: {duplicates_found}")
                print(f"   Original expenses: {original_count}")
                print(f"   After deduplication: {len(unique_expenses)}")
                expenses = unique_expenses
                modified = True
                stats['duplicates_removed'] += duplicates_found
            
            # Strategy 2: Recalculate total_manual_expenses
            calculated_total = sum(safe_float(exp.get('amount', 0)) for exp in expenses)
            stored_total = original_total
            
            tolerance = 1.0  # 1 kr tolerance for rounding
            if abs(calculated_total - stored_total) > tolerance:
                print(f"\n🔧 Property: {prop.name}")
                print(f"   Stored total: {stored_total:,.2f} kr")
                print(f"   Calculated total: {calculated_total:,.2f} kr")
                print(f"   Difference: {abs(calculated_total - stored_total):,.2f} kr")
                print(f"   → Recalculating total")
                modified = True
                stats['totals_recalculated'] += 1
            
            # Strategy 3: Fix zero totals with data
            if len(expenses) > 0 and stored_total == 0 and calculated_total > 0:
                print(f"\n⚠️  Property: {prop.name}")
                print(f"   Has {len(expenses)} expenses but total is 0")
                print(f"   Calculated total: {calculated_total:,.2f} kr")
                print(f"   → Fixing zero total")
                modified = True
                stats['zero_totals_fixed'] += 1
            
            # Apply changes if modified
            if modified and not dry_run:
                financials['manual_expenses'] = expenses
                financials['total_manual_expenses'] = calculated_total
                prop.external_data['financials'] = financials
                flag_modified(prop, 'external_data')
                stats['properties_modified'] += 1
                modified_properties.append(prop.name)
            elif modified and dry_run:
                stats['properties_modified'] += 1
                modified_properties.append(prop.name)
        
        # Commit changes if not dry run
        if not dry_run:
            await db.commit()
            print("\n" + "=" * 100)
            print("✅ CHANGES COMMITTED TO DATABASE")
            print("=" * 100)
        else:
            print("\n" + "=" * 100)
            print("ℹ️  DRY RUN COMPLETE - NO CHANGES MADE")
            print("=" * 100)
        
        # Print summary
        print("\nSUMMARY:")
        print(f"  Properties analyzed: {len(properties)}")
        print(f"  Properties modified: {stats['properties_modified']}")
        print(f"  Duplicates removed: {stats['duplicates_removed']}")
        print(f"  Totals recalculated: {stats['totals_recalculated']}")
        print(f"  Zero totals fixed: {stats['zero_totals_fixed']}")
        
        if modified_properties:
            print(f"\nModified properties:")
            for name in sorted(modified_properties):
                print(f"  - {name}")
        
        if dry_run:
            print(f"\n💡 To apply these changes, run with --apply flag")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fix financial data discrepancies')
    parser.add_argument('--apply', action='store_true', help='Apply fixes (default is dry-run)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (default)')
    args = parser.parse_args()
    
    # Default to dry-run unless --apply is specified
    dry_run = not args.apply
    
    asyncio.run(fix_financial_discrepancies(dry_run=dry_run))
