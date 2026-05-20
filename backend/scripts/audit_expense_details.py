#!/usr/bin/env python3
"""
Deep-dive audit to analyze expense patterns and detect duplicates
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


async def audit_expense_details():
    print("=" * 100)
    print("DETAILED EXPENSE PATTERN ANALYSIS")
    print("=" * 100)
    
    async with SessionLocal() as db:
        stmt = select(Property)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        duplicate_stats = []
        source_stats = []
        quarterly_patterns = []
        
        for prop in properties:
            ext = prop.external_data or {}
            financials = ext.get('financials', {})
            expenses = financials.get('manual_expenses', [])
            
            if not expenses:
                continue
            
            # 1. Detect duplicates
            expense_signatures = defaultdict(int)
            for exp in expenses:
                # Create a signature from key fields
                sig = (
                    exp.get('date', ''),
                    exp.get('type', ''),
                    exp.get('amount', 0),
                    exp.get('provider', '')
                )
                expense_signatures[sig] += 1
            
            duplicates = {sig: count for sig, count in expense_signatures.items() if count > 1}
            if duplicates:
                total_dup_amount = sum(sig[2] * (count - 1) for sig, count in duplicates.items())
                duplicate_stats.append({
                    'name': prop.name,
                    'duplicates': len(duplicates),
                    'total_duplicate_amount': total_dup_amount,
                    'details': duplicates
                })
            
            # 2. Analyze by source file
            by_source = defaultdict(list)
            for exp in expenses:
                source = exp.get('source', 'unknown')
                by_source[source].append(exp)
            
            if len(by_source) > 0:
                source_stats.append({
                    'name': prop.name,
                    'sources': {src: len(exps) for src, exps in by_source.items()},
                    'total_expenses': len(expenses)
                })
            
            # 3. Detect quarterly patterns
            by_quarter = defaultdict(list)
            for exp in expenses:
                date = exp.get('date', '')
                if 'Q' in str(date):
                    by_quarter[date].append(exp)
            
            if by_quarter:
                total_quarterly = sum(len(exps) for exps in by_quarter.values())
                quarterly_patterns.append({
                    'name': prop.name,
                    'quarters': {q: len(exps) for q, exps in by_quarter.items()},
                    'total_quarterly': total_quarterly,
                    'pct_quarterly': 100 * total_quarterly / len(expenses)
                })
        
        # Print results
        print(f"\n🔍 1. DUPLICATE DETECTION")
        print(f"   Found {len(duplicate_stats)} properties with duplicates\n")
        
        if duplicate_stats:
            sorted_dups = sorted(duplicate_stats, key=lambda x: -x['total_duplicate_amount'])
            for entry in sorted_dups[:10]:
                print(f"   Property: {entry['name']}")
                print(f"   Unique duplicates: {entry['duplicates']}")
                print(f"   Total duplicate amount: {entry['total_duplicate_amount']:,.0f} kr")
                print(f"   Sample duplicates:")
                for sig, count in list(entry['details'].items())[:3]:
                    date, typ, amount, provider = sig
                    print(f"     - {date} | {typ} | {amount:,.0f} kr | {provider} (x{count})")
                print()
        
        print(f"\n📁 2. SOURCE FILE ANALYSIS")
        print(f"   Properties with expenses from multiple sources: {sum(1 for s in source_stats if len(s['sources']) > 1)}\n")
        
        multi_source = [s for s in source_stats if len(s['sources']) > 1]
        for entry in sorted(multi_source, key=lambda x: -x['total_expenses'])[:10]:
            print(f"   Property: {entry['name']}")
            print(f"   Total expenses: {entry['total_expenses']}")
            print(f"   Sources:")
            for src, count in sorted(entry['sources'].items(), key=lambda x: -x[1]):
                print(f"     - {src}: {count} items")
            print()
        
        print(f"\n📊 3. QUARTERLY PATTERN DETECTION")
        print(f"   Properties with quarterly-dated expenses: {len(quarterly_patterns)}\n")
        
        for entry in sorted(quarterly_patterns, key=lambda x: -x['pct_quarterly'])[:10]:
            print(f"   Property: {entry['name']}")
            print(f"   Quarterly expenses: {entry['total_quarterly']} ({entry['pct_quarterly']:.1f}%)")
            print(f"   Breakdown:")
            for quarter, count in sorted(entry['quarters'].items()):
                print(f"     - {quarter}: {count} items")
            print()
        
        # Export detailed report
        export_dir = os.path.join(os.path.dirname(__file__), '..')
        with open(os.path.join(export_dir, 'expense_details_report.txt'), 'w', encoding='utf-8') as f:
            f.write("DETAILED EXPENSE PATTERN ANALYSIS\n")
            f.write("=" * 100 + "\n\n")
            
            f.write("DUPLICATES:\n")
            f.write("-" * 100 + "\n")
            for entry in sorted(duplicate_stats, key=lambda x: -x['total_duplicate_amount']):
                f.write(f"\nProperty: {entry['name']}\n")
                f.write(f"Unique duplicates: {entry['duplicates']}\n")
                f.write(f"Total duplicate amount: {entry['total_duplicate_amount']:,.0f} kr\n")
                f.write("Details:\n")
                for sig, count in entry['details'].items():
                    date, typ, amount, provider = sig
                    f.write(f"  {date} | {typ} | {amount:,.0f} kr | {provider} (x{count})\n")
            
            f.write(f"\n\nSOURCE FILE ANALYSIS:\n")
            f.write("-" * 100 + "\n")
            for entry in sorted(source_stats, key=lambda x: -x['total_expenses']):
                f.write(f"\nProperty: {entry['name']}\n")
                f.write(f"Total expenses: {entry['total_expenses']}\n")
                for src, count in sorted(entry['sources'].items(), key=lambda x: -x[1]):
                    f.write(f"  {src}: {count} items\n")
            
            f.write(f"\n\nQUARTERLY PATTERNS:\n")
            f.write("-" * 100 + "\n")
            for entry in sorted(quarterly_patterns, key=lambda x: -x['pct_quarterly']):
                f.write(f"\nProperty: {entry['name']}\n")
                f.write(f"Quarterly expenses: {entry['total_quarterly']} ({entry['pct_quarterly']:.1f}%)\n")
                for quarter, count in sorted(entry['quarters'].items()):
                    f.write(f"  {quarter}: {count} items\n")
        
        print(f"\n✅ Exported to: expense_details_report.txt")


if __name__ == "__main__":
    asyncio.run(audit_expense_details())
