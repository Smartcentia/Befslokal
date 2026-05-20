#!/usr/bin/env python3
"""
Analyze negative amounts in financial transactions to identify:
1. Legitimate credit notes/corrections
2. Import errors
3. Patterns in negative amounts
"""

import sys
import os
import asyncio
from collections import defaultdict
from sqlalchemy import select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property

async def analyze_negatives():
    print("=" * 80)
    print("ANALYZING NEGATIVE AMOUNTS")
    print("=" * 80)
    
    async with SessionLocal() as db:
        stmt = select(Property).where(Property.external_data.is_not(None))
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        # Statistics
        total_negative = 0
        negative_by_category = defaultdict(int)
        negative_by_provider = defaultdict(int)
        negative_by_property = defaultdict(list)
        small_negatives = []  # < -1000
        large_negatives = []  # < -10000
        
        for prop in properties:
            ext = prop.external_data or {}
            expenses = ext.get('financials', {}).get('manual_expenses', [])
            
            for exp in expenses:
                try:
                    amount = float(exp.get('amount', 0) or 0)
                except (ValueError, TypeError):
                    amount = 0.0
                
                if amount < 0:
                    total_negative += 1
                    category = exp.get('type', 'Ukjent')
                    provider = exp.get('provider', 'Ukjent')
                    source = exp.get('source', 'Unknown')
                    
                    negative_by_category[category] += 1
                    negative_by_provider[provider] += 1
                    
                    entry = {
                        'property': prop.name,
                        'amount': amount,
                        'provider': provider,
                        'category': category,
                        'source': source
                    }
                    
                    negative_by_property[prop.name].append(entry)
                    
                    if amount < -10000:
                        large_negatives.append(entry)
                    elif amount < -1000:
                        small_negatives.append(entry)
        
        print(f"\n📊 OVERALL STATISTICS")
        print(f"Total negative amounts found: {total_negative}")
        print(f"Properties affected: {len(negative_by_property)}")
        
        print(f"\n📋 TOP 10 CATEGORIES WITH NEGATIVE AMOUNTS")
        sorted_categories = sorted(negative_by_category.items(), key=lambda x: -x[1])
        for cat, count in sorted_categories[:10]:
            percentage = (count / total_negative) * 100
            print(f"  {cat[:50]:<50} {count:>5} ({percentage:>5.1f}%)")
        
        print(f"\n📋 TOP 10 PROVIDERS WITH NEGATIVE AMOUNTS")
        sorted_providers = sorted(negative_by_provider.items(), key=lambda x: -x[1])
        for prov, count in sorted_providers[:10]:
            percentage = (count / total_negative) * 100
            print(f"  {prov[:50]:<50} {count:>5} ({percentage:>5.1f}%)")
        
        print(f"\n⚠️ LARGE NEGATIVE AMOUNTS (< -10,000 kr): {len(large_negatives)}")
        if large_negatives:
            print("\nTop 10 largest negatives:")
            sorted_large = sorted(large_negatives, key=lambda x: x['amount'])
            for entry in sorted_large[:10]:
                print(f"  {entry['property'][:40]:<40} {entry['amount']:>12,.0f} kr")
                print(f"    Provider: {entry['provider']}")
                print(f"    Category: {entry['category']}")
                print(f"    Source: {entry['source']}")
                print()
        
        print(f"\n📊 PROPERTIES WITH MOST NEGATIVE AMOUNTS")
        sorted_props = sorted(negative_by_property.items(), key=lambda x: -len(x[1]))
        for prop_name, entries in sorted_props[:10]:
            print(f"\n  {prop_name}")
            print(f"    Negative transactions: {len(entries)}")
            total_neg = sum(e['amount'] for e in entries)
            print(f"    Total negative: {total_neg:,.0f} kr")
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        
        # Identify likely patterns
        print("\n🔍 PATTERN ANALYSIS:")
        
        # Check if negatives are concentrated in specific categories
        top_cat_percent = (sorted_categories[0][1] / total_negative) * 100 if sorted_categories else 0
        if top_cat_percent > 50:
            print(f"  ⚠️ {sorted_categories[0][1]} negatives ({top_cat_percent:.1f}%) are in '{sorted_categories[0][0]}'")
            print(f"     This suggests a systematic pattern - likely credit notes or corrections")
        
        # Check proportion of large vs small negatives
        large_pct = (len(large_negatives) / total_negative) * 100 if total_negative > 0 else 0
        print(f"\n  Large negatives (< -10K): {len(large_negatives)} ({large_pct:.1f}%)")
        print(f"  Small negatives (> -10K): {total_negative - len(large_negatives)} ({100-large_pct:.1f}%)")
        
        if large_pct > 20:
            print(f"     ⚠️ High proportion of large negatives suggests potential import errors")
        else:
            print(f"     ✅ Most negatives are small - likely legitimate corrections")

if __name__ == "__main__":
    asyncio.run(analyze_negatives())
