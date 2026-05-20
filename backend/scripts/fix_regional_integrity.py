#!/usr/bin/env python3
"""
Conservative fix for regional integrity issues.

Strategy:
1. Skip properties with "Unknown" region (can't determine what's wrong)
2. Skip properties where >50% of data is from wrong region (would lose too much)
3. Only remove wrong-region data from properties with <50% wrong data
4. Log all removals for review
"""

import sys
import os
import asyncio
import re
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import attributes

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property

# File to Region Mapping
FILE_REGION_MAP = {
    'docs/01.txt': '05 - Midt-Norge',
    'docs/02.txt': '05 - Midt-Norge',
    'docs/03.txt': '05 - Midt-Norge',
    'docs/04.txt': '05 - Midt-Norge',
    'docs/05.txt': '05 - Midt-Norge',
    'docs/06.txt': '02 - Øst',
    'docs/07.txt': '05 - Midt-Norge',
    'docs/08.txt': '04 - Vest',
    'docs/09.txt': '02 - Øst',
    'docs/10.txt': '05 - Midt-Norge',
    'docs/11.txt': '04 - Vest',
    'docs/12.txt': '02 - Øst',
    'docs/13.txt': '02 - Øst',
    'docs/14.txt': '03 - Sør',
    'docs/15.txt': '04 - Vest',
    'docs/16.txt': '02 - Øst',
    'docs/17.txt': '03 - Sør'
}

def region_matches(prop_region: str, file_region: str) -> bool:
    """Check if property region matches file region."""
    if not prop_region or prop_region.lower() == 'unknown':
        return False  # Can't determine match for unknown
    
    prop_reg_lower = prop_region.lower()
    file_parts = file_region.split(' - ')
    region_code = file_parts[0]
    region_name = file_parts[1].lower() if len(file_parts) > 1 else ""
    
    return region_code in prop_reg_lower or region_name in prop_reg_lower

async def fix_regional_integrity():
    print("=" * 80)
    print("CONSERVATIVE REGIONAL INTEGRITY FIX")
    print("=" * 80)
    print("\nStrategy:")
    print("  ✓ Skip properties with 'Unknown' region")
    print("  ✓ Skip properties with >50% wrong data")
    print("  ✓ Only fix properties with clear wrong-region data")
    print()
    
    async with SessionLocal() as db:
        stmt = select(Property).where(Property.external_data.is_not(None))
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        # Statistics
        properties_fixed = 0
        properties_skipped_unknown = 0
        properties_skipped_too_much_wrong = 0
        properties_skipped_safe = 0
        total_removed = 0
        
        log_entries = []
        
        for prop in properties:
            ext = prop.external_data or {}
            fin = ext.get('financials', {})
            expenses = fin.get('manual_expenses', [])
            
            if not expenses:
                continue
            
            prop_region = str(prop.region) if prop.region else "Unknown"
            
            # SKIP: Unknown region
            if prop_region.lower() == 'unknown':
                properties_skipped_unknown += 1
                continue
            
            # Analyze this property
            wrong_region_expenses = []
            correct_region_expenses = []
            
            for exp in expenses:
                source = exp.get('source', 'Unknown')
                match = re.search(r'docs/\d+\.txt', source)
                
                if not match:
                    correct_region_expenses.append(exp)  # Keep if no source
                    continue
                
                filename = match.group(0)
                file_region = FILE_REGION_MAP.get(filename)
                
                if not file_region:
                    correct_region_expenses.append(exp)  # Keep if unknown file
                    continue
                
                if region_matches(prop_region, file_region):
                    correct_region_expenses.append(exp)
                else:
                    wrong_region_expenses.append((exp, file_region))
            
            # Calculate percentage wrong
            if len(expenses) == 0:
                continue
            
            pct_wrong = (len(wrong_region_expenses) / len(expenses)) * 100
            
            # SKIP: >50% wrong (too risky)
            if pct_wrong > 50:
                properties_skipped_too_much_wrong += 1
                log_entries.append(f"SKIPPED (>{pct_wrong:.0f}% wrong): {prop.name} - would lose {len(wrong_region_expenses)}/{len(expenses)} transactions")
                continue
            
            # SKIP: No wrong data
            if len(wrong_region_expenses) == 0:
                properties_skipped_safe += 1
                continue
            
            # FIX: Remove wrong-region data
            print(f"\n🔧 Fixing '{prop.name}'")
            print(f"   Region: {prop_region}")
            print(f"   Total: {len(expenses)}, Wrong: {len(wrong_region_expenses)} ({pct_wrong:.1f}%), Keeping: {len(correct_region_expenses)}")
            
            for exp, file_region in wrong_region_expenses[:5]:  # Show first 5
                amount = exp.get('amount', 0)
                provider = exp.get('provider', 'Ukjent')
                category = exp.get('type', 'Ukjent')
                print(f"     ❌ Removing from '{file_region}': {amount:,.0f} kr - {category} ({provider})")
            
            if len(wrong_region_expenses) > 5:
                print(f"     ... and {len(wrong_region_expenses) - 5} more")
            
            # Update property
            new_ext = dict(ext)
            new_fin = dict(new_ext.get('financials', {}))
            new_fin['manual_expenses'] = correct_region_expenses
            
            # Recalculate total
            total = sum(float(e.get('amount', 0) or 0) for e in correct_region_expenses)
            new_fin['total_manual_expenses'] = total
            
            new_ext['financials'] = new_fin
            prop.external_data = new_ext
            attributes.flag_modified(prop, 'external_data')
            
            properties_fixed += 1
            total_removed += len(wrong_region_expenses)
            
            log_entries.append(f"FIXED: {prop.name} - removed {len(wrong_region_expenses)}/{len(expenses)} wrong-region transactions")
        
        # Commit
        await db.commit()
        
        print("\n" + "=" * 80)
        print("FIX SUMMARY")
        print("=" * 80)
        print(f"✅ Properties fixed: {properties_fixed}")
        print(f"✅ Wrong-region transactions removed: {total_removed}")
        print(f"⏭️  Properties skipped (Unknown region): {properties_skipped_unknown}")
        print(f"⏭️  Properties skipped (>50% wrong - too risky): {properties_skipped_too_much_wrong}")
        print(f"✓  Properties skipped (no wrong data): {properties_skipped_safe}")
        
        # Write log
        log_file = os.path.join(os.path.dirname(__file__), '..', 'regional_fix_log.txt')
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("REGIONAL INTEGRITY FIX LOG\n")
            f.write("=" * 80 + "\n\n")
            for entry in log_entries:
                f.write(entry + "\n")
        
        print(f"\n📝 Detailed log written to: {log_file}")
        print(f"\n🎉 Fix completed successfully!")
        
        if properties_skipped_too_much_wrong > 0:
            print(f"\n⚠️  WARNING: {properties_skipped_too_much_wrong} properties were skipped")
            print(f"   These need manual review - they have >50% wrong-region data")
            print(f"   Consider updating their region or manually reviewing the data")

if __name__ == "__main__":
    asyncio.run(fix_regional_integrity())
