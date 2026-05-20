#!/usr/bin/env python3
"""
Intelligent auto-fix script for financial data
Implements all fixes identified by advanced analysis
"""

import sys
import os
import asyncio
import argparse
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
import statistics

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property


def safe_float(value, default=0.0):
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


async def intelligent_auto_fix(dry_run=True, enable_all=False, 
                               fix_pairs=False, fix_scale=False, 
                               fix_duplicates=False, fix_outliers=False):
    """
    Intelligent auto-fix based on pattern analysis
    
    Args:
        dry_run: If True, only simulate changes
        enable_all: Enable all fixes
        fix_pairs: Fix correction pairs
        fix_scale: Fix scale errors
        fix_duplicates: Fix aggressive duplicates
        fix_outliers: Fix statistical outliers
    """
    
    if enable_all:
        fix_pairs = fix_scale = fix_duplicates = fix_outliers = True
    
    print("=" * 100)
    print("INTELLIGENT AUTO-FIX - IMPLEMENTERING AV ALLE IDENTIFISERTE FIKSER")
    print("=" * 100)
    print(f"Mode: {'DRY RUN' if dry_run else '🔴 LIVE - ENDRER DATABASE'}")
    print(f"Aktiverte fikser:")
    print(f"  ✓ Korreksjonspar: {'JA' if fix_pairs else 'NEI'}")
    print(f"  ✓ Skalafeil: {'JA' if fix_scale else 'NEI'}")
    print(f"  ✓ Aggressive duplikater: {'JA' if fix_duplicates else 'NEI'}")
    print(f"  ✓ Statistiske outliers: {'JA' if fix_outliers else 'NEI'}")
    print("=" * 100)
    
    async with SessionLocal() as db:
        stmt = select(Property)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        stats = {
            'properties_modified': 0,
            'pairs_removed': 0,
            'scale_fixed': 0,
            'duplicates_removed': 0,
            'outliers_removed': 0,
            'total_amount_saved': 0,
        }
        
        # Collect category medians for scale detection
        category_medians = {}
        if fix_scale:
            print("\n📊 Beregner kategori-medianer for skalafeildeteksjon...")
            for prop in properties:
                ext = prop.external_data or {}
                financials = ext.get('financials', {})
                expenses = financials.get('manual_expenses', [])
                
                for exp in expenses:
                    category = exp.get('type', 'Unknown')
                    amount = safe_float(exp.get('amount', 0))
                    if amount > 0:
                        if category not in category_medians:
                            category_medians[category] = []
                        category_medians[category].append(amount)
            
            # Calculate medians
            for cat in category_medians:
                if len(category_medians[cat]) >= 10:
                    category_medians[cat] = statistics.median(category_medians[cat])
                else:
                    category_medians[cat] = None
        
        # Calculate category stats for outlier detection
        category_stats = {}
        if fix_outliers:
            print("\n📈 Beregner statistikk for outlier-deteksjon...")
            category_amounts = defaultdict(list)
            for prop in properties:
                ext = prop.external_data or {}
                financials = ext.get('financials', {})
                expenses = financials.get('manual_expenses', [])
                
                for exp in expenses:
                    category = exp.get('type', 'Unknown')
                    amount = safe_float(exp.get('amount', 0))
                    category_amounts[category].append(amount)
            
            for cat, amounts in category_amounts.items():
                if len(amounts) >= 20:
                    mean = statistics.mean(amounts)
                    stdev = statistics.stdev(amounts)
                    category_stats[cat] = {'mean': mean, 'stdev': stdev}
        
        # Process each property
        for prop in properties:
            ext = prop.external_data or {}
            financials = ext.get('financials', {})
            expenses = financials.get('manual_expenses', [])
            
            if not expenses:
                continue
            
            original_count = len(expenses)
            original_total = safe_float(financials.get('total_manual_expenses', 0))
            
            modified = False
            new_expenses = []
            
            # Track amounts by category for pair detection
            if fix_pairs:
                category_amounts = defaultdict(list)
                for exp in expenses:
                    category = exp.get('type', 'Unknown')
                    amount = safe_float(exp.get('amount', 0))
                    category_amounts[category].append((amount, exp))
            
            # Track for duplicate detection
            if fix_duplicates:
                seen_signatures = set()
            
            for exp in expenses:
                amount = safe_float(exp.get('amount', 0))
                category = exp.get('type', 'Unknown')
                provider = exp.get('provider', 'Ukjent')
                date = exp.get('date', '')
                
                should_keep = True
                reason = None
                
                # FIX 1: Check for correction pairs
                if fix_pairs and should_keep:
                    # Check if this amount has an exact opposite in same category
                    opposite = -amount
                    for other_amount, other_exp in category_amounts.get(category, []):
                        if abs(other_amount - opposite) < 0.01 and other_exp != exp:
                            should_keep = False
                            reason = f"Korreksjonspar: {amount:,.0f} kr"
                            stats['pairs_removed'] += 1
                            modified = True
                            break
                
                # FIX 2: Check for scale errors
                if fix_scale and should_keep and amount > 0:
                    median = category_medians.get(category)
                    if median and median > 0:
                        ratios = [10, 100, 12, 4]  # Check for 10x, 100x, 12x (monthly), 4x (quarterly)
                        for ratio in ratios:
                            expected = median * ratio
                            if abs(amount - expected) < expected * 0.1:  # Within 10%
                                # Fix: divide by ratio
                                exp['amount'] = amount / ratio
                                exp['original_amount'] = amount
                                exp['fix_applied'] = f'DIVIDED_BY_{ratio}'
                                should_keep = True
                                stats['scale_fixed'] += 1
                                stats['total_amount_saved'] += amount - (amount / ratio)
                                modified = True
                                break
                
                # FIX 3: Check for duplicates
                if fix_duplicates and should_keep:
                    signature = (
                        provider,
                        category,
                        round(amount, 2),
                        date[:7] if date else ''
                    )
                    
                    if signature in seen_signatures:
                        should_keep = False
                        reason = f"Duplikat: {amount:,.0f} kr"
                        stats['duplicates_removed'] += 1
                        stats['total_amount_saved'] += abs(amount)
                        modified = True
                    else:
                        seen_signatures.add(signature)
                
                # FIX 4: Check for statistical outliers
                if fix_outliers and should_keep:
                    cat_stats = category_stats.get(category)
                    if cat_stats:
                        mean = cat_stats['mean']
                        stdev = cat_stats['stdev']
                        if stdev > 0:
                            z_score = abs((amount - mean) / stdev)
                            if z_score > 5:  # More than 5 standard deviations
                                should_keep = False
                                reason = f"Outlier: {z_score:.1f}σ"
                                stats['outliers_removed'] += 1
                                stats['total_amount_saved'] += abs(amount)
                                modified = True
                
                if should_keep:
                    new_expenses.append(exp)
            
            # Update if modified
            if modified:
                financials['manual_expenses'] = new_expenses
                calculated_total = sum(safe_float(exp.get('amount', 0)) for exp in new_expenses)
                financials['total_manual_expenses'] = calculated_total
                
                if not dry_run:
                    prop.external_data['financials'] = financials
                    flag_modified(prop, 'external_data')
                
                stats['properties_modified'] += 1
                
                print(f"\n✓ {prop.name[:70]}")
                print(f"  Før: {original_count} poster, {original_total:,.0f} kr")
                print(f"  Etter: {len(new_expenses)} poster, {calculated_total:,.0f} kr")
                print(f"  Spart: {original_total - calculated_total:,.0f} kr")
        
        # Commit if not dry run
        if not dry_run:
            await db.commit()
            print("\n" + "=" * 100)
            print("✅ ENDRINGER LAGRET I DATABASE")
            print("=" * 100)
        else:
            print("\n" + "=" * 100)
            print("ℹ️  DRY RUN - INGEN ENDRINGER LAGRET")
            print("=" * 100)
        
        # Final summary
        print("\n" + "=" * 100)
        print("OPPSUMMERING")
        print("=" * 100)
        print(f"Eiendommer modifisert: {stats['properties_modified']}")
        print(f"Korreksjonspar fjernet: {stats['pairs_removed']}")
        print(f"Skalafeil rettet: {stats['scale_fixed']}")
        print(f"Duplikater fjernet: {stats['duplicates_removed']}")
        print(f"Outliers fjernet: {stats['outliers_removed']}")
        print(f"Totalt beløp spart: {stats['total_amount_saved']:,.0f} kr")
        
        if dry_run:
            print(f"\n💡 For å faktisk kjøre fiksene, kjør med --apply")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Intelligent auto-fix for financial data')
    parser.add_argument('--apply', action='store_true', help='Apply fixes (default is dry-run)')
    parser.add_argument('--all', action='store_true', help='Enable all fixes')
    parser.add_argument('--pairs', action='store_true', help='Fix correction pairs')
    parser.add_argument('--scale', action='store_true', help='Fix scale errors')
    parser.add_argument('--duplicates', action='store_true', help='Fix duplicates')
    parser.add_argument('--outliers', action='store_true', help='Fix outliers')
    
    args = parser.parse_args()
    
    asyncio.run(intelligent_auto_fix(
        dry_run=not args.apply,
        enable_all=args.all,
        fix_pairs=args.pairs,
        fix_scale=args.scale,
        fix_duplicates=args.duplicates,
        fix_outliers=args.outliers
    ))
