#!/usr/bin/env python3
"""
Advanced financial data analysis with pattern recognition and intelligent auto-fix suggestions
This script takes more risks and provides actionable recommendations
"""

import sys
import os
import asyncio
from collections import defaultdict, Counter
from sqlalchemy import select
import statistics
import re

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


async def advanced_financial_analysis():
    print("=" * 100)
    print("AVANSERT FINANSIELL ANALYSE MED INTELLIGENT AUTO-FIX")
    print("=" * 100)
    print("⚠️  DENNE ANALYSEN TAR FLERE RISIKOER OG GIR AGGRESSIVE ANBEFALINGER")
    print("=" * 100)
    
    async with SessionLocal() as db:
        stmt = select(Property)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        # Data structures for analysis
        all_expenses = []
        negative_patterns = defaultdict(list)
        provider_patterns = defaultdict(lambda: {'positive': [], 'negative': []})
        category_patterns = defaultdict(lambda: {'positive': [], 'negative': []})
        duplicate_candidates = []
        
        # Collect all expense data
        for prop in properties:
            ext = prop.external_data or {}
            financials = ext.get('financials', {})
            expenses = financials.get('manual_expenses', [])
            
            for exp in expenses:
                amount = safe_float(exp.get('amount', 0))
                exp_type = exp.get('type', 'Unknown')
                provider = exp.get('provider', 'Ukjent')
                date = exp.get('date', '')
                
                expense_data = {
                    'property': prop.name,
                    'property_id': prop.property_id,
                    'region': prop.region or 'Unknown',
                    'amount': amount,
                    'type': exp_type,
                    'provider': provider,
                    'date': date,
                    'source': exp.get('source', ''),
                }
                
                all_expenses.append(expense_data)
                
                # Track provider patterns
                if amount < 0:
                    provider_patterns[provider]['negative'].append(amount)
                    negative_patterns[exp_type].append(expense_data)
                else:
                    provider_patterns[provider]['positive'].append(amount)
                
                # Track category patterns
                if amount < 0:
                    category_patterns[exp_type]['negative'].append(amount)
                else:
                    category_patterns[exp_type]['positive'].append(amount)
        
        print(f"\n📊 Totalt {len(all_expenses):,} utgiftsposter analysert")
        print(f"   Eiendommer: {len(properties)}")
        
        # ANALYSIS 1: Paired negative/positive detection
        print("\n" + "=" * 100)
        print("1. OPPDAGELSE AV SAMMENKOBLEDE POSITIVE/NEGATIVE PAR")
        print("=" * 100)
        print("Leter etter negative beløp som har eksakt motsatt positivt beløp...")
        
        # Group by property and category
        property_category_amounts = defaultdict(lambda: defaultdict(list))
        for exp in all_expenses:
            key = (exp['property_id'], exp['type'])
            property_category_amounts[key]['amounts'].append(exp['amount'])
        
        potential_pairs = []
        for key, data in property_category_amounts.items():
            amounts = data['amounts']
            negatives = [a for a in amounts if a < 0]
            positives = [a for a in amounts if a > 0]
            
            for neg in negatives:
                # Look for exact positive match
                if abs(neg) in positives:
                    potential_pairs.append({
                        'property_id': key[0],
                        'category': key[1],
                        'negative': neg,
                        'positive': abs(neg),
                        'action': 'REMOVE_BOTH'  # Likely correction entries
                    })
        
        print(f"\n🎯 Funnet {len(potential_pairs)} sannsynlige korreksjonspar")
        if potential_pairs:
            print(f"\n   Top 10 eksempler:")
            for pair in sorted(potential_pairs, key=lambda x: abs(x['negative']))[:10]:
                print(f"     Kategori: {pair['category'][:50]}")
                print(f"     Beløp: {pair['negative']:,.0f} kr og +{pair['positive']:,.0f} kr")
                print(f"     → ANBEFALING: Fjern begge (korreksjon)")
                print()
        
        # ANALYSIS 2: Provider analysis - who always gives negatives?
        print("=" * 100)
        print("2. LEVERANDØRANALYSE - IDENTIFISER KREDITTGIVERE")
        print("=" * 100)
        
        always_negative_providers = []
        mostly_negative_providers = []
        
        for provider, data in provider_patterns.items():
            if provider == 'Ukjent':
                continue
            
            neg_count = len(data['negative'])
            pos_count = len(data['positive'])
            total = neg_count + pos_count
            
            if total < 3:  # Skip providers with too few entries
                continue
            
            neg_pct = (neg_count / total) * 100 if total > 0 else 0
            
            if neg_count > 0 and pos_count == 0:
                always_negative_providers.append({
                    'provider': provider,
                    'count': neg_count,
                    'total_amount': sum(data['negative']),
                    'action': 'CONVERT_TO_ABS'  # Likely credits/refunds
                })
            elif neg_pct > 80:
                mostly_negative_providers.append({
                    'provider': provider,
                    'neg_count': neg_count,
                    'pos_count': pos_count,
                    'pct_negative': neg_pct,
                    'total_negative': sum(data['negative'])
                })
        
        print(f"\n🔍 Leverandører som KUN gir negative beløp ({len(always_negative_providers)}):")
        if always_negative_providers:
            for prov in sorted(always_negative_providers, key=lambda x: x['total_amount'])[:15]:
                print(f"\n   {prov['provider'][:60]}")
                print(f"   Antall: {prov['count']}, Totalt: {prov['total_amount']:,.0f} kr")
                print(f"   → ANBEFALING: Konverter til absoluttverdier (sannsynlig kreditt)")
        
        # ANALYSIS 3: Extreme ratio detection
        print("\n" + "=" * 100)
        print("3. EKSTREME FORHOLD - IDENTIFISER SKALAFEIL")
        print("=" * 100)
        print("Ser etter beløp som er akkurat 10x, 100x, 1000x større enn normalt...")
        
        scale_errors = []
        
        for category, data in category_patterns.items():
            if len(data['positive']) < 10:
                continue
            
            positives = data['positive']
            median_positive = statistics.median(positives)
            
            # Check for values that are exactly 10x, 100x, 1000x the median
            for amount in positives:
                ratios = [10, 100, 1000, 4, 12]  # Include 4 (quarterly) and 12 (monthly)
                for ratio in ratios:
                    expected = median_positive * ratio
                    if abs(amount - expected) < expected * 0.1:  # Within 10% of expected
                        scale_errors.append({
                            'category': category,
                            'amount': amount,
                            'median': median_positive,
                            'ratio': ratio,
                            'suggested_fix': amount / ratio,
                            'action': f'DIVIDE_BY_{ratio}'
                        })
        
        print(f"\n⚠️  Funnet {len(scale_errors)} potensielle skalafeil")
        if scale_errors:
            print(f"\n   Top 20 eksempler:")
            for err in sorted(scale_errors, key=lambda x: -x['amount'])[:20]:
                print(f"\n   Kategori: {err['category'][:50]}")
                print(f"   Beløp: {err['amount']:,.0f} kr (median: {err['median']:,.0f} kr)")
                print(f"   Ratio: {err['ratio']}x median")
                print(f"   → ANBEFALING: Del på {err['ratio']} = {err['suggested_fix']:,.0f} kr")
        
        # ANALYSIS 4: Duplicate detection (more aggressive)
        print("\n" + "=" * 100)
        print("4. AGGRESSIV DUPLIKATDETEKSJON")
        print("=" * 100)
        print("Ser etter like beløp fra samme leverandør i samme periode...")
        
        # Group by property, provider, type, amount
        signature_groups = defaultdict(list)
        for exp in all_expenses:
            sig = (
                exp['property_id'],
                exp['provider'],
                exp['type'],
                round(exp['amount'], 2),  # Round to avoid floating point issues
                exp['date'][:7] if exp['date'] else ''  # Year-month only
            )
            signature_groups[sig].append(exp)
        
        aggressive_duplicates = []
        for sig, exps in signature_groups.items():
            if len(exps) > 1:
                aggressive_duplicates.append({
                    'count': len(exps),
                    'property': exps[0]['property'],
                    'provider': sig[1],
                    'type': sig[2],
                    'amount': sig[3],
                    'total_duplicate': sig[3] * (len(exps) - 1),
                    'action': f'REMOVE_{len(exps)-1}_DUPLICATES'
                })
        
        print(f"\n🔍 Funnet {len(aggressive_duplicates)} duplikatgrupper")
        if aggressive_duplicates:
            total_saved = sum(d['total_duplicate'] for d in aggressive_duplicates)
            print(f"   Totalt duplikat beløp: {total_saved:,.0f} kr")
            print(f"\n   Top 15 duplikatgrupper:")
            for dup in sorted(aggressive_duplicates, key=lambda x: -x['total_duplicate'])[:15]:
                print(f"\n   {dup['property'][:50]}")
                print(f"   {dup['type'][:40]} - {dup['provider'][:30]}")
                print(f"   {dup['count']}x {dup['amount']:,.0f} kr = {dup['count'] * dup['amount']:,.0f} kr")
                print(f"   → ANBEFALING: Fjern {dup['count']-1} duplikater, spar {dup['total_duplicate']:,.0f} kr")
        
        # ANALYSIS 5: Outlier removal recommendation
        print("\n" + "=" * 100)
        print("5. STATISTISK OUTLIER-FJERNING")
        print("=" * 100)
        print("Identifiser ekstreme outliers som bør fjernes...")
        
        outliers_to_remove = []
        
        for category, data in category_patterns.items():
            all_amounts = data['positive'] + data['negative']
            if len(all_amounts) < 20:
                continue
            
            mean = statistics.mean(all_amounts)
            stdev = statistics.stdev(all_amounts)
            
            for amount in all_amounts:
                z_score = abs((amount - mean) / stdev) if stdev > 0 else 0
                if z_score > 5:  # More than 5 standard deviations
                    outliers_to_remove.append({
                        'category': category,
                        'amount': amount,
                        'mean': mean,
                        'z_score': z_score,
                        'action': 'REMOVE_OUTLIER'
                    })
        
        print(f"\n📊 Funnet {len(outliers_to_remove)} ekstreme outliers (>5σ)")
        if outliers_to_remove:
            print(f"\n   Top 20 outliers:")
            for out in sorted(outliers_to_remove, key=lambda x: -x['z_score'])[:20]:
                print(f"\n   Kategori: {out['category'][:50]}")
                print(f"   Beløp: {out['amount']:,.0f} kr (gjennomsnitt: {out['mean']:,.0f} kr)")
                print(f"   Z-score: {out['z_score']:.1f}σ")
                print(f"   → ANBEFALING: Fjern (ekstrem outlier)")
        
        # Generate action plan
        print("\n" + "=" * 100)
        print("OPPSUMMERING OG HANDLINGSPLAN")
        print("=" * 100)
        
        total_issues = (
            len(potential_pairs) +
            len(always_negative_providers) +
            len(scale_errors) +
            len(aggressive_duplicates) +
            len(outliers_to_remove)
        )
        
        print(f"\n📋 Totalt {total_issues} automatiserbare fikser identifisert:")
        print(f"   1. Korreksjonspar (fjern begge): {len(potential_pairs)}")
        print(f"   2. Kredittleverandører (konverter): {len(always_negative_providers)}")
        print(f"   3. Skalafeil (del på X): {len(scale_errors)}")
        print(f"   4. Aggressive duplikater: {len(aggressive_duplicates)}")
        print(f"   5. Ekstreme outliers: {len(outliers_to_remove)}")
        
        # Export recommendations
        export_dir = os.path.join(os.path.dirname(__file__), '..')
        with open(os.path.join(export_dir, 'advanced_analysis_recommendations.txt'), 'w', encoding='utf-8') as f:
            f.write("AVANSERT ANALYSE - AUTOMATISERBARE FIKSER\n")
            f.write("=" * 100 + "\n\n")
            
            f.write(f"KORREKSJONSPAR ({len(potential_pairs)}):\n")
            f.write("-" * 100 + "\n")
            for pair in potential_pairs:
                f.write(f"Kategori: {pair['category']}\n")
                f.write(f"Beløp: {pair['negative']:,.2f} og {pair['positive']:,.2f}\n")
                f.write(f"Action: {pair['action']}\n\n")
            
            f.write(f"\n\nKREDITTLEVERANDØRER ({len(always_negative_providers)}):\n")
            f.write("-" * 100 + "\n")
            for prov in always_negative_providers:
                f.write(f"Leverandør: {prov['provider']}\n")
                f.write(f"Antall: {prov['count']}, Totalt: {prov['total_amount']:,.2f} kr\n")
                f.write(f"Action: {prov['action']}\n\n")
            
            f.write(f"\n\nSKALAFEIL ({len(scale_errors)}):\n")
            f.write("-" * 100 + "\n")
            for err in sorted(scale_errors, key=lambda x: -x['amount']):
                f.write(f"Kategori: {err['category']}\n")
                f.write(f"Beløp: {err['amount']:,.2f} kr → {err['suggested_fix']:,.2f} kr\n")
                f.write(f"Action: {err['action']}\n\n")
        
        print(f"\n✅ Detaljert rapport eksportert til: advanced_analysis_recommendations.txt")
        print(f"\n⚡ NESTE STEG: Generer auto-fix script basert på disse anbefalingene")


if __name__ == "__main__":
    asyncio.run(advanced_financial_analysis())
