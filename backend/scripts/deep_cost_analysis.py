#!/usr/bin/env python3
"""
Deep cost analysis to identify additional data quality issues
"""

import sys
import os
import asyncio
from collections import defaultdict
from sqlalchemy import select
import statistics

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


async def deep_cost_analysis():
    print("=" * 100)
    print("DEEP COST ANALYSIS - IDENTIFYING ANOMALIES")
    print("=" * 100)
    
    async with SessionLocal() as db:
        stmt = select(Property)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        # Collect all cost data
        cost_by_category = defaultdict(list)
        property_costs = []
        expense_patterns = []
        
        for prop in properties:
            ext = prop.external_data or {}
            financials = ext.get('financials', {})
            expenses = financials.get('manual_expenses', [])
            
            if not expenses:
                continue
            
            total_cost = safe_float(financials.get('total_manual_expenses', 0))
            
            # Analyze by category/type
            category_totals = defaultdict(float)
            for exp in expenses:
                expense_type = exp.get('type', 'Unknown')
                amount = safe_float(exp.get('amount', 0))
                category_totals[expense_type] += amount
                cost_by_category[expense_type].append(amount)
            
            property_costs.append({
                'name': prop.name,
                'region': prop.region or 'Unknown',
                'total': total_cost,
                'expense_count': len(expenses),
                'categories': category_totals,
                'avg_per_expense': total_cost / len(expenses) if expenses else 0
            })
            
            # Track expense patterns
            expense_patterns.append({
                'name': prop.name,
                'expenses': expenses,
                'categories': len(category_totals)
            })
        
        print(f"\n📊 Analyzed {len(property_costs)} properties with cost data\n")
        
        # Analysis 1: Outliers by category
        print("=" * 100)
        print("1. EXTREME VALUES BY COST CATEGORY")
        print("=" * 100)
        
        category_stats = {}
        for category, amounts in cost_by_category.items():
            if len(amounts) < 5:  # Skip categories with too few data points
                continue
            
            amounts_sorted = sorted(amounts)
            median = statistics.median(amounts)
            mean = statistics.mean(amounts)
            stdev = statistics.stdev(amounts) if len(amounts) > 1 else 0
            
            # Find outliers (>3 standard deviations from mean)
            outliers = [a for a in amounts if abs(a - mean) > 3 * stdev] if stdev > 0 else []
            
            category_stats[category] = {
                'count': len(amounts),
                'median': median,
                'mean': mean,
                'stdev': stdev,
                'min': min(amounts),
                'max': max(amounts),
                'outliers': len(outliers)
            }
        
        # Show categories with most outliers
        categories_with_outliers = {k: v for k, v in category_stats.items() if v['outliers'] > 0}
        
        print(f"\nFound {len(categories_with_outliers)} categories with extreme values:\n")
        
        for category in sorted(categories_with_outliers.keys(), key=lambda x: -categories_with_outliers[x]['outliers'])[:10]:
            stats = categories_with_outliers[category]
            print(f"Category: {category}")
            print(f"  Outliers: {stats['outliers']} / {stats['count']} expenses")
            print(f"  Normal range: {stats['mean'] - 3*stats['stdev']:,.0f} - {stats['mean'] + 3*stats['stdev']:,.0f} kr")
            print(f"  Actual range: {stats['min']:,.0f} - {stats['max']:,.0f} kr")
            print()
        
        # Analysis 2: Suspiciously round numbers
        print("=" * 100)
        print("2. SUSPICIOUSLY ROUND NUMBERS (potential estimates)")
        print("=" * 100)
        
        round_number_properties = []
        
        for prop_data in property_costs:
            if prop_data['expense_count'] < 3:
                continue
            
            # Count how many expenses are round numbers
            round_count = 0
            for exp_type, amount in prop_data['categories'].items():
                # Check if number is very round (divisible by 1000, 10000, etc)
                if amount > 0:
                    if amount % 100000 == 0:
                        round_count += 3  # Very suspicious
                    elif amount % 10000 == 0:
                        round_count += 2
                    elif amount % 1000 == 0:
                        round_count += 1
            
            round_pct = (round_count / len(prop_data['categories'])) * 100 if prop_data['categories'] else 0
            
            if round_pct > 50:  # More than 50% are round numbers
                round_number_properties.append({
                    'name': prop_data['name'],
                    'round_score': round_count,
                    'total_categories': len(prop_data['categories']),
                    'round_pct': round_pct
                })
        
        print(f"\nFound {len(round_number_properties)} properties with many round numbers:\n")
        
        for entry in sorted(round_number_properties, key=lambda x: -x['round_score'])[:15]:
            print(f"  {entry['name'][:70]:70} Score: {entry['round_score']}, {entry['round_pct']:.0f}% round")
        
        # Analysis 3: Unusually high average expense
        print("\n" + "=" * 100)
        print("3. UNUSUALLY HIGH AVERAGE EXPENSE PER ITEM")
        print("=" * 100)
        
        avg_expenses = [p['avg_per_expense'] for p in property_costs if p['avg_per_expense'] > 0]
        if avg_expenses:
            median_avg = statistics.median(avg_expenses)
            
            high_avg_properties = [
                p for p in property_costs 
                if p['avg_per_expense'] > median_avg * 5  # 5x median
            ]
            
            print(f"\nMedian average expense: {median_avg:,.0f} kr")
            print(f"Found {len(high_avg_properties)} properties with avg >5x median:\n")
            
            for entry in sorted(high_avg_properties, key=lambda x: -x['avg_per_expense'])[:15]:
                print(f"  {entry['name'][:60]:60} Avg: {entry['avg_per_expense']:>12,.0f} kr  ({entry['expense_count']} items)")
        
        # Analysis 4: Missing common cost categories
        print("\n" + "=" * 100)
        print("4. MISSING COMMON COST CATEGORIES")
        print("=" * 100)
        
        # Find most common categories
        all_categories = set()
        for prop_data in property_costs:
            all_categories.update(prop_data['categories'].keys())
        
        category_frequency = {cat: 0 for cat in all_categories}
        for prop_data in property_costs:
            for cat in prop_data['categories'].keys():
                category_frequency[cat] += 1
        
        # Common categories are those in >30% of properties
        common_categories = {
            cat: freq for cat, freq in category_frequency.items() 
            if freq > len(property_costs) * 0.3
        }
        
        print(f"\nCommon cost categories (in >30% of properties):")
        for cat in sorted(common_categories.keys(), key=lambda x: -common_categories[x]):
            print(f"  - {cat}: in {common_categories[cat]}/{len(property_costs)} properties ({100*common_categories[cat]/len(property_costs):.0f}%)")
        
        # Find properties missing these common categories
        print(f"\nProperties missing common categories:\n")
        
        missing_common = []
        for prop_data in property_costs:
            if prop_data['total'] > 100000:  # Only check properties with significant costs
                missing = [cat for cat in common_categories.keys() if cat not in prop_data['categories']]
                if len(missing) >= 3:  # Missing 3+ common categories
                    missing_common.append({
                        'name': prop_data['name'],
                        'missing': missing,
                        'missing_count': len(missing)
                    })
        
        for entry in sorted(missing_common, key=lambda x: -x['missing_count'])[:20]:
            print(f"  {entry['name'][:60]:60} Missing {entry['missing_count']} categories")
            for cat in entry['missing'][:5]:
                print(f"    - {cat}")
        
        # Analysis 5: Zero or negative amounts
        print("\n" + "=" * 100)
        print("5. ZERO OR NEGATIVE AMOUNTS")
        print("=" * 100)
        
        zero_negative_issues = []
        
        for prop in properties:
            ext = prop.external_data or {}
            financials = ext.get('financials', {})
            expenses = financials.get('manual_expenses', [])
            
            issues = []
            for exp in expenses:
                amount = safe_float(exp.get('amount', 0))
                if amount <= 0:
                    issues.append(exp)
            
            if issues:
                zero_negative_issues.append({
                    'name': prop.name,
                    'issues': issues
                })
        
        print(f"\nFound {len(zero_negative_issues)} properties with zero/negative amounts:\n")
        
        for entry in zero_negative_issues[:10]:
            print(f"  Property: {entry['name']}")
            for issue in entry['issues'][:3]:
                print(f"    - {issue.get('type', 'Unknown')}: {issue.get('amount', 0)} kr")
        
        # Export detailed report
        export_dir = os.path.join(os.path.dirname(__file__), '..')
        with open(os.path.join(export_dir, 'deep_cost_analysis_report.txt'), 'w', encoding='utf-8') as f:
            f.write("DEEP COST ANALYSIS REPORT\n")
            f.write("=" * 100 + "\n\n")
            
            f.write("CATEGORIES WITH OUTLIERS:\n")
            f.write("-" * 100 + "\n")
            for category, stats in sorted(categories_with_outliers.items(), key=lambda x: -x[1]['outliers']):
                f.write(f"\n{category}:\n")
                f.write(f"  Outliers: {stats['outliers']}/{stats['count']}\n")
                f.write(f"  Range: {stats['min']:,.0f} - {stats['max']:,.0f} kr\n")
                f.write(f"  Mean ± 3σ: {stats['mean']:,.0f} ± {3*stats['stdev']:,.0f} kr\n")
            
            f.write(f"\n\nROUND NUMBER PROPERTIES:\n")
            f.write("-" * 100 + "\n")
            for entry in sorted(round_number_properties, key=lambda x: -x['round_score']):
                f.write(f"{entry['name']}: score {entry['round_score']}\n")
            
            f.write(f"\n\nHIGH AVERAGE EXPENSE:\n")
            f.write("-" * 100 + "\n")
            for entry in sorted(high_avg_properties, key=lambda x: -x['avg_per_expense']):
                f.write(f"{entry['name']}: {entry['avg_per_expense']:,.0f} kr avg ({entry['expense_count']} items)\n")
            
            f.write(f"\n\nMISSING COMMON CATEGORIES:\n")
            f.write("-" * 100 + "\n")
            for entry in sorted(missing_common, key=lambda x: -x['missing_count']):
                f.write(f"\n{entry['name']}:\n")
                for cat in entry['missing']:
                    f.write(f"  - {cat}\n")
            
            f.write(f"\n\nZERO/NEGATIVE AMOUNTS:\n")
            f.write("-" * 100 + "\n")
            for entry in zero_negative_issues:
                f.write(f"\n{entry['name']}:\n")
                for issue in entry['issues']:
                    f.write(f"  - {issue.get('type', 'Unknown')}: {issue.get('amount', 0)} kr\n")
        
        print(f"\n✅ Exported detailed report to: deep_cost_analysis_report.txt")
        
        # Summary
        print("\n" + "=" * 100)
        print("SUMMARY")
        print("=" * 100)
        print(f"Categories with outliers: {len(categories_with_outliers)}")
        print(f"Properties with round numbers: {len(round_number_properties)}")
        print(f"Properties with high avg expense: {len(high_avg_properties)}")
        print(f"Properties missing common categories: {len(missing_common)}")
        print(f"Properties with zero/negative amounts: {len(zero_negative_issues)}")


if __name__ == "__main__":
    asyncio.run(deep_cost_analysis())
