#!/usr/bin/env python3
"""
Deep analysis of regional integrity issues to understand:
1. Which properties have wrong regional data
2. Which source files are being incorrectly mapped
3. Scale of the problem per region
4. Whether this can be fixed or needs re-import
"""

import sys
import os
import asyncio
import re
from collections import defaultdict
from sqlalchemy import select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property

# File to Region Mapping (Cleaned to standard names)
FILE_REGION_MAP = {
    'docs/01.txt': 'Midt-Norge',
    'docs/02.txt': 'Midt-Norge',
    'docs/03.txt': 'Midt-Norge',
    'docs/04.txt': 'Midt-Norge',
    'docs/05.txt': 'Midt-Norge',
    'docs/06.txt': 'Øst',
    'docs/07.txt': 'Midt-Norge',
    'docs/08.txt': 'Vest',
    'docs/09.txt': 'Øst',
    'docs/10.txt': 'Midt-Norge',
    'docs/11.txt': 'Vest',
    'docs/12.txt': 'Øst',
    'docs/13.txt': 'Øst',
    'docs/14.txt': 'Sør',
    'docs/15.txt': 'Vest',
    'docs/16.txt': 'Øst',
    'docs/17.txt': 'Sør'
}

async def analyze_regional_integrity():
    print("=" * 80)
    print("DEEP REGIONAL INTEGRITY ANALYSIS")
    print("=" * 80)
    
    async with SessionLocal() as db:
        stmt = select(Property).where(Property.external_data.is_not(None))
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        # Statistics
        total_mismatches = 0
        mismatches_by_property = defaultdict(lambda: {'count': 0, 'files': set(), 'expected_regions': set()})
        mismatches_by_file = defaultdict(int)
        mismatches_by_region = defaultdict(lambda: defaultdict(int))  # actual_region -> expected_region -> count
        
        properties_with_issues = []
        
        for prop in properties:
            ext = prop.external_data or {}
            expenses = ext.get('financials', {}).get('manual_expenses', [])
            
            if not expenses:
                continue
            
            prop_region = str(prop.region) if prop.region else "Unknown"
            prop_mismatches = 0
            
            for exp in expenses:
                source = exp.get('source', 'Unknown')
                
                # Extract filename
                match = re.search(r'docs/\d+\.txt', source)
                if not match:
                    continue
                
                filename = match.group(0)
                expected_region = FILE_REGION_MAP.get(filename)
                
                if not expected_region:
                    continue
                
                # Normalize for comparison using standard core utility
                from app.domains.core.utils.region_mapping import get_operational_region
                normalized_prop_region = get_operational_region(prop_region)
                
                # Check if match (case-insensitive for safety)
                is_match = normalized_prop_region.lower() == expected_region.lower()
                
                if not is_match:
                    total_mismatches += 1
                    prop_mismatches += 1
                    
                    mismatches_by_property[prop.name]['count'] += 1
                    mismatches_by_property[prop.name]['files'].add(filename)
                    mismatches_by_property[prop.name]['expected_regions'].add(expected_region)
                    
                    mismatches_by_file[filename] += 1
                    mismatches_by_region[prop_region][expected_region] += 1
            
            if prop_mismatches > 0:
                properties_with_issues.append({
                    'name': prop.name,
                    'region': prop_region,
                    'mismatches': prop_mismatches,
                    'total_expenses': len(expenses),
                    'percentage': (prop_mismatches / len(expenses)) * 100
                })
        
        print(f"\n📊 OVERALL STATISTICS")
        print(f"Total regional mismatches: {total_mismatches:,}")
        print(f"Properties affected: {len(mismatches_by_property)}")
        print(f"Properties with issues: {len(properties_with_issues)}")
        
        print(f"\n📋 PROPERTIES MOST AFFECTED (Top 15)")
        print(f"{'Property':<50} {'Region':<20} {'Mismatches':<12} {'%':<6}")
        print("-" * 90)
        sorted_props = sorted(properties_with_issues, key=lambda x: -x['mismatches'])
        for p in sorted_props[:15]:
            print(f"{p['name'][:48]:<50} {p['region']:<20} {p['mismatches']:>10,} {p['percentage']:>5.1f}%")
        
        print(f"\n📋 MISMATCHES BY SOURCE FILE")
        sorted_files = sorted(mismatches_by_file.items(), key=lambda x: -x[1])
        for filename, count in sorted_files:
            expected = FILE_REGION_MAP.get(filename, "Unknown")
            print(f"  {filename:<15} → {expected:<20} {count:>6,} mismatches")
        
        print(f"\n📋 ACTUAL REGION → EXPECTED REGION MAPPING")
        for actual_region, expected_regions in sorted(mismatches_by_region.items()):
            print(f"\n  Properties in '{actual_region}':")
            for expected_region, count in sorted(expected_regions.items(), key=lambda x: -x[1]):
                print(f"    ← Data from '{expected_region}': {count:,} transactions")
        
        print(f"\n🔍 PATTERN ANALYSIS:")
        
        # Check if there are clear wrong mappings
        print(f"\n  Properties with >90% wrong data:")
        high_percentage = [p for p in properties_with_issues if p['percentage'] > 90]
        if high_percentage:
            for p in high_percentage[:10]:
                prop_data = mismatches_by_property[p['name']]
                files = ', '.join(prop_data['files'])
                regions = ', '.join(prop_data['expected_regions'])
                print(f"    {p['name'][:45]}")
                print(f"      Region: {p['region']}, Data from: {regions}")
                print(f"      {p['mismatches']}/{p['total_expenses']} transactions ({p['percentage']:.1f}%)")
        else:
            print(f"    None - Most properties have mixed data")
        
        # Identify if re-import is needed or if we can fix
        print(f"\n  Assessment:")
        severely_affected = len([p for p in properties_with_issues if p['percentage'] > 50])
        print(f"    - Properties with >50% wrong data: {severely_affected}")
        
        if severely_affected > 20:
            print(f"    ⚠️ CRITICAL: Re-import recommended")
            print(f"       Too many properties have majority wrong data")
        else:
            print(f"    ✅ Can potentially fix by removing wrong-region data")
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(analyze_regional_integrity())
