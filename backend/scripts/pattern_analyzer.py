#!/usr/bin/env python3
"""
Pattern Analysis Extension for Cost Analyzer

Commands:
  python pattern_analyzer.py similar <property_name>  - Find most similar properties
  python pattern_analyzer.py patterns                 - Find common cost patterns
  python pattern_analyzer.py patterns extended        - Extended patterns (regional, supplier, time, etc.)
  python pattern_analyzer.py validate                 - Find outliers and potential errors
"""

import sys
import os
import asyncio
from collections import defaultdict
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


async def find_similar_properties(property_name):
    """Find properties with similar cost structures"""
    print("📊 Loading data and analyzing similarities...")
    
    async with SessionLocal() as db:
        # Get all properties
        stmt_prop = select(Property)
        result_prop = await db.execute(stmt_prop)
        properties = result_prop.scalars().all()
        
        # Get all active contracts
        stmt_contract = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        result_contract = await db.execute(stmt_contract)
        contracts = result_contract.scalars().all()
        
        # Build property data
        property_data = {}
        property_contracts = {}
        
        for contract in contracts:
            if contract.unit and contract.unit.property:
                prop_id = contract.unit.property.property_id
                if prop_id not in property_contracts:
                    property_contracts[prop_id] = []
                property_contracts[prop_id].append(contract)
        
        for prop in properties:
            prop_id = prop.property_id
            
            # Get rent
            total_rent = 0
            if prop_id in property_contracts:
                for contract in property_contracts[prop_id]:
                    amount_data = contract.amount if isinstance(contract.amount, dict) else {}
                    rent = amount_data.get('amount_per_year', 0)
                    try:
                        rent = float(rent) if rent else 0
                    except:
                        rent = 0
                    total_rent += rent
            
            # Get costs
            ext = prop.external_data or {}
            expenses = ext.get('financials', {}).get('manual_expenses', [])
            
            total_costs = 0
            cost_by_category = defaultdict(float)
            
            for exp in expenses:
                try:
                    amount = float(exp.get('amount', 0) or 0)
                    total_costs += amount
                    category = exp.get('type', 'Ukjent')
                    cost_by_category[category] += amount
                except:
                    pass
            
            # Normalize cost structure (percentages)
            cost_structure = {}
            if total_costs > 0:
                for cat, amount in cost_by_category.items():
                    cost_structure[cat] = (amount / total_costs) * 100
            
            property_data[prop.name.lower()] = {
                'name': prop.name,
                'region': prop.region or 'Unknown',
                'rent': total_rent,
                'costs': total_costs,
                'total': total_rent + total_costs,
                'cost_structure': cost_structure,
                'num_expenses': len(expenses)
            }
        
        # Find the target property
        target_name = property_name.lower()
        target = None
        
        for key, data in property_data.items():
            if target_name in key:
                target = data
                break
        
        if not target:
            print(f"❌ Property '{property_name}' not found")
            return
        
        print(f"\n🎯 Target Property: {target['name']}")
        print(f"   Region: {target['region']}")
        print(f"   Rent: {target['rent']:,.0f} kr")
        print(f"   Costs: {target['costs']:,.0f} kr")
        print(f"   Total: {target['total']:,.0f} kr")
        
        # Calculate similarity scores
        similarities = []
        
        for data in property_data.values():
            if data['name'] == target['name']:
                continue  # Skip self
            
            # Skip properties without data
            if data['costs'] == 0 or target['costs'] == 0:
                continue
            
            # Calculate similarity score
            score = 0
            factors = []
            
            # 1. Region match (30 points)
            if data['region'] == target['region'] and target['region'] != 'Unknown':
                score += 30
                factors.append("Same region")
            
            # 2. Similar total cost (30 points)
            if target['total'] > 0 and data['total'] > 0:
                ratio = min(target['total'], data['total']) / max(target['total'], data['total'])
                cost_score = ratio * 30
                score += cost_score
                if ratio > 0.8:
                    factors.append(f"Similar total cost ({ratio*100:.0f}% match)")
            
            # 3. Similar cost structure (40 points)
            structure_score = 0
            all_categories = set(target['cost_structure'].keys()) | set(data['cost_structure'].keys())
            
            if all_categories:
                for cat in all_categories:
                    target_pct = target['cost_structure'].get(cat, 0)
                    data_pct = data['cost_structure'].get(cat, 0)
                    
                    # Penalize difference
                    diff = abs(target_pct - data_pct)
                    structure_score += max(0, (100 - diff) / len(all_categories))
                
                structure_score = (structure_score / 100) * 40
                score += structure_score
                
                if structure_score > 25:
                    factors.append(f"Similar cost categories")
            
            similarities.append({
                'name': data['name'],
                'region': data['region'],
                'score': score,
                'rent': data['rent'],
                'costs': data['costs'],
                'total': data['total'],
                'factors': factors
            })
        
        # Sort by score
        similarities.sort(key=lambda x: -x['score'])
        
        print(f"\n🔍 TOP 15 MOST SIMILAR PROPERTIES:")
        print(f"\n{'Rank':<5} {'Score':<7} {'Property':<45} {'Region':<20} {'Total':>15}")
        print("-" * 100)
        
        for i, sim in enumerate(similarities[:15], 1):
            print(f"{i:<5} {sim['score']:>5.1f}%  {sim['name'][:43]:<45} {sim['region']:<20} {sim['total']:>15,.0f}")
            if sim['factors']:
                print(f"       Reasons: {', '.join(sim['factors'])}")
        
        # Show detailed comparison with top 3
        print(f"\n📊 DETAILED COMPARISON WITH TOP 3:")
        
        for i, sim in enumerate(similarities[:3], 1):
            print(f"\n{i}. {sim['name']} (Score: {sim['score']:.1f}%)")
            print(f"   Region: {sim['region']}")
            print(f"   Rent: {sim['rent']:,.0f} kr (vs {target['rent']:,.0f})")
            print(f"   Costs: {sim['costs']:,.0f} kr (vs {target['costs']:,.0f})")
            print(f"   Total: {sim['total']:,.0f} kr (vs {target['total']:,.0f})")


async def find_cost_patterns():
    """Identify common cost patterns and clusters"""
    print("📊 Loading data and identifying patterns...")
    
    async with SessionLocal() as db:
        stmt_prop = select(Property)
        result_prop = await db.execute(stmt_prop)
        properties = result_prop.scalars().all()
        
        # Analyze cost categories
        category_frequency = defaultdict(int)
        category_amounts = defaultdict(list)
        provider_frequency = defaultdict(int)
        
        for prop in properties:
            ext = prop.external_data or {}
            expenses = ext.get('financials', {}).get('manual_expenses', [])
            
            categories_in_prop = set()
            
            for exp in expenses:
                category = exp.get('type', 'Ukjent')
                provider = exp.get('provider', 'Ukjent')
                
                try:
                    amount = float(exp.get('amount', 0) or 0)
                except:
                    amount = 0
                
                if category not in categories_in_prop:
                    category_frequency[category] += 1
                    categories_in_prop.add(category)
                
                category_amounts[category].append(amount)
                provider_frequency[provider] += 1
        
        print(f"\n" + "=" * 80)
        print("COMMON COST PATTERNS")
        print("=" * 80)
        
        print(f"\n📋 TOP 20 MOST COMMON COST CATEGORIES:")
        print(f"   (Present in X properties)")
        print()
        
        sorted_cats = sorted(category_frequency.items(), key=lambda x: -x[1])
        for cat, count in sorted_cats[:20]:
            pct = (count / len(properties)) * 100
            avg_amount = sum(category_amounts[cat]) / len(category_amounts[cat])
            print(f"   {cat[:50]:<50} {count:>4} properties ({pct:>5.1f}%) - Avg: {avg_amount:>10,.0f} kr")
        
        print(f"\n🏢 TOP 15 MOST COMMON PROVIDERS:")
        sorted_provs = sorted(provider_frequency.items(), key=lambda x: -x[1])
        for prov, count in sorted_provs[:15]:
            print(f"   {prov[:50]:<50} {count:>4} properties")
        
        # Identify property clusters by cost structure
        print(f"\n📊 PROPERTY CLUSTERS BY COST PROFILE:")
        
        # Simple clustering: group by dominant category
        dominant_category = defaultdict(list)
        
        for prop in properties:
            ext = prop.external_data or {}
            expenses = ext.get('financials', {}).get('manual_expenses', [])
            
            if not expenses:
                continue
            
            cost_by_category = defaultdict(float)
            total = 0
            
            for exp in expenses:
                try:
                    amount = float(exp.get('amount', 0) or 0)
                    category = exp.get('type', 'Ukjent')
                    cost_by_category[category] += amount
                    total += amount
                except:
                    pass
            
            if total > 0:
                # Find dominant category
                max_cat = max(cost_by_category.items(), key=lambda x: x[1])
                pct = (max_cat[1] / total) * 100
                
                if pct > 40:  # Dominant if >40%
                    dominant_category[max_cat[0]].append({
                        'name': prop.name,
                        'pct': pct,
                        'amount': max_cat[1]
                    })
        
        print(f"\n   Properties grouped by dominant cost category (>40% of total):")
        for cat in sorted(dominant_category.keys(), key=lambda x: -len(dominant_category[x]))[:10]:
            props = dominant_category[cat]
            print(f"\n   {cat} ({len(props)} properties):")
            for p in sorted(props, key=lambda x: -x['amount'])[:5]:
                print(f"      - {p['name'][:50]} ({p['pct']:.1f}%)")


async def validate_data():
    """Find potential data errors and outliers"""
    print("📊 Loading data and validating...")
    
    async with SessionLocal() as db:
        stmt_prop = select(Property)
        result_prop = await db.execute(stmt_prop)
        properties = result_prop.scalars().all()
        
        stmt_contract = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        result_contract = await db.execute(stmt_contract)
        contracts = result_contract.scalars().all()
        
        print(f"\n" + "=" * 80)
        print("DATA VALIDATION - POTENTIAL ERRORS")
        print("=" * 80)
        
        # 1. Same property name but different IDs (duplicates?)
        name_to_ids = defaultdict(list)
        for prop in properties:
            name_to_ids[prop.name.lower()].append(prop.property_id)
        
        duplicates = {name: ids for name, ids in name_to_ids.items() if len(ids) > 1}
        
        if duplicates:
            print(f"\n🚨 DUPLICATE PROPERTY NAMES ({len(duplicates)}):")
            for name, ids in sorted(duplicates.items())[:10]:
                print(f"   '{name}' appears {len(ids)} times")
        
        # 2. Properties with costs but wrong region (Unknown)
        unknown_with_data = []
        for prop in properties:
            if not prop.region or str(prop.region).lower() == 'unknown':
                ext = prop.external_data or {}
                expenses = ext.get('financials', {}).get('manual_expenses', [])
                
                if expenses:
                    total = sum(float(e.get('amount', 0) or 0) for e in expenses)
                    if total > 100000:  # Significant costs
                        unknown_with_data.append({
                            'name': prop.name,
                            'costs': total,
                            'num_trans': len(expenses)
                        })
        
        if unknown_with_data:
            print(f"\n⚠️  PROPERTIES WITH HIGH COSTS BUT UNKNOWN REGION ({len(unknown_with_data)}):")
            for p in sorted(unknown_with_data, key=lambda x: -x['costs'])[:10]:
                print(f"   {p['name'][:50]:<50} {p['costs']:>12,.0f} kr ({p['num_trans']} trans)")
        
        # 3. Extreme outliers in cost-to-rent ratio
        print(f"\n🔍 EXTREME OUTLIERS:")
        
        property_contracts = {}
        for contract in contracts:
            if contract.unit and contract.unit.property:
                prop_id = contract.unit.property.property_id
                if prop_id not in property_contracts:
                    property_contracts[prop_id] = []
                property_contracts[prop_id].append(contract)
        
        outliers = []
        for prop in properties:
            # Get rent
            total_rent = 0
            if prop.property_id in property_contracts:
                for contract in property_contracts[prop.property_id]:
                    amount_data = contract.amount if isinstance(contract.amount, dict) else {}
                    rent = amount_data.get('amount_per_year', 0)
                    try:
                        rent = float(rent) if rent else 0
                    except:
                        rent = 0
                    total_rent += rent
            
            # Get costs
            ext = prop.external_data or {}
            expenses = ext.get('financials', {}).get('manual_expenses', [])
            total_costs = sum(float(e.get('amount', 0) or 0) for e in expenses)
            
            if total_rent > 0 and total_costs > 0:
                ratio = total_costs / total_rent
                
                # Extreme: costs are >200% of rent
                if ratio > 2.0:
                    outliers.append({
                        'name': prop.name,
                        'rent': total_rent,
                        'costs': total_costs,
                        'ratio': ratio
                    })
        
        if outliers:
            print(f"\n   Properties where costs > 200% of rent:")
            for o in sorted(outliers, key=lambda x: -x['ratio'])[:10]:
                print(f"   {o['name'][:45]:<45} Ratio: {o['ratio']:.1f}x")
                print(f"      Rent: {o['rent']:>10,.0f} kr, Costs: {o['costs']:>10,.0f} kr")


async def find_extended_patterns():
    """Kjør utvidede kostnadsmønstre via FinancialAnalysisService."""
    from app.services.analytics.financial_analysis_service import FinancialAnalysisService

    print("📊 Henter utvidede kostnadsmønstre...")
    async with SessionLocal() as db:
        patterns = await FinancialAnalysisService.get_common_patterns(db)

    def p(name):
        print(f"\n{'='*80}\n{name}\n{'='*80}")

    # Regional
    rp = patterns.get('regional_patterns', {})
    if rp:
        p("GEOGRAFISKE MØNSTRE")
        for reg in rp.get('by_region', [])[:10]:
            cps = f", {reg['cost_per_sqm']:.0f} kr/kvm" if reg.get('cost_per_sqm') else ""
            print(f"  {reg['region']}: {reg['property_count']} eiendommer, snitt {reg['avg_costs']:,.0f} kr{cps}")
        ab = rp.get('above_below_regional_avg', [])[:5]
        if ab:
            print("\n  Største avvik fra regionalt snitt:")
            for x in ab:
                print(f"    {x['property'][:50]}: {x['deviation_pct']:+.1f}%")

    # Leverandørkoncentration
    sc = patterns.get('supplier_concentration', {})
    if sc:
        p("LEVERANDØRKONCENTRASJON")
        few = sc.get('few_suppliers', [])[:5]
        if few:
            print("  Få leverandører (1-2):")
            for x in few:
                print(f"    {x['property'][:50]}: {x['supplier_count']} lev, {x['total_costs']:,.0f} kr")
        high = sc.get('high_concentration', [])[:5]
        if high:
            print("  Høy koncentration (>50% fra én leverandør):")
            for x in high:
                print(f"    {x['property'][:50]}: {x['top_provider'][:30]} ({x['share_pct']}%)")

    # Leverandørprisvariasjon
    spv = patterns.get('supplier_price_variation', {})
    if spv:
        p("LEVERANDØRPRISVARIASJON")
        for x in spv.get('by_provider', [])[:8]:
            print(f"  {x['provider'][:45]}: CV={x['coefficient_of_variation_pct']}%, snitt {x['mean_amount']:,.0f} kr")

    # Tidsmønstre
    tp = patterns.get('time_patterns', {})
    if tp:
        p("TIDSMØNSTRE")
        print(f"  Date-dekning: {tp.get('date_coverage_pct', 0)}%")
        for y in tp.get('by_year', [])[:5]:
            print(f"  År {y['year']}: {y['total']:,.0f} kr")

    # Kategori-bundles
    cb = patterns.get('category_bundles', {})
    if cb:
        p("KATEGORI-KOMBINASJONER")
        for b in cb.get('common_bundles', [])[:8]:
            print(f"  {b['categories']}: {b['property_count']} eiendommer")

    # Skaleringsmønstre
    sp = patterns.get('scaling_patterns', {})
    if sp:
        p("SKALERINGSMØNSTRE (kostnad per kvm)")
        for x in sp.get('cost_per_sqm', [])[:8]:
            print(f"  {x['property'][:50]}: {x['cost_per_sqm']:.0f} kr/kvm")

    # Cluster
    cp = patterns.get('cluster_patterns', {})
    if cp:
        p("CLUSTER-ANALYSE")
        for c in cp.get('clusters', []):
            print(f"  {c['label']}: {c['property_count']} eiendommer")
            for prop in c.get('properties', [])[:3]:
                print(f"    - {prop[:50]}")

    # 9. Bygningsalder
    bap = patterns.get('building_age_patterns', {})
    if bap:
        p("BYGNINGSALDER VS KOSTNAD")
        for x in bap.get('by_age_bucket', []):
            print(f"  {x['age_bucket']} år: {x['property_count']} eiendommer, snitt {x['avg_costs']:,.0f} kr")

    # 10. Energimerking
    elp = patterns.get('energy_label_patterns', {})
    if elp:
        p("ENERGIMERKING VS KOSTNAD")
        for x in elp.get('by_energy_label', [])[:8]:
            print(f"  {x['label']}: {x['property_count']} eiendommer, snitt {x['avg_costs']:,.0f} kr")

    # 11. Brukstype
    utp = patterns.get('usage_type_patterns', {})
    if utp:
        p("BRUKSTYPE VS KOSTNAD")
        for x in utp.get('by_usage', [])[:8]:
            print(f"  {x['usage'][:40]}: {x['property_count']} eiendommer, snitt {x['avg_costs']:,.0f} kr")

    # 12. Kostnad per kvm per kategori
    cpsc = patterns.get('cost_per_sqm_by_category', {})
    if cpsc:
        p("KOSTNAD PER KVM PER KATEGORI")
        for x in cpsc.get('by_category', []):
            print(f"  {x['category']}: snitt {x['avg_per_sqm']:.0f} kr/kvm ({x['property_count']} eiendommer)")

    # 13. Budsjett vs faktisk
    bvp = patterns.get('budget_variance_patterns', {})
    if bvp and bvp.get('variances'):
        p("BUDSJETT VS FAKTISK (VARIANS)")
        for x in bvp.get('variances', [])[:5]:
            print(f"  {x['property'][:50]}: budsjett {x['budget']:,.0f}, faktisk {x['actual']:,.0f}, varians {x['variance_pct']:+.1f}%")

    # 14. Risiko-kostnad
    rcp = patterns.get('risk_cost_patterns', {})
    if rcp and rcp.get('priority_list'):
        p("RISIKO-KOSTNAD (PRIORITERINGSINDEKS)")
        for x in rcp.get('priority_list', [])[:5]:
            print(f"  {x['property'][:50]}: risiko {x['risk_score']}, indeks {x['priority_index']:,.0f}")

    # 15. Leverandørportefølje-overlap
    sop = patterns.get('supplier_overlap_patterns', {})
    if sop and sop.get('overlap_pairs'):
        p("LEVERANDØRPORTEFØLJE-OVERLAP")
        for x in sop.get('overlap_pairs', [])[:5]:
            print(f"  {x['property_a'][:25]} <-> {x['property_b'][:25]}: Jaccard {x['jaccard']:.2f}")

    # 16. Manglende data
    mdp = patterns.get('missing_data_patterns', {})
    if mdp:
        p("MANGLENDE DATA")
        print(f"  Høy husleie uten kostnader: {len(mdp.get('high_rent_no_costs', []))}")
        print(f"  Høye kostnader uten husleie: {len(mdp.get('high_costs_no_rent', []))}")
        print(f"  Utgifter uten date: {mdp.get('expenses_without_date', 0)} av {mdp.get('total_expenses', 0)}")
        print(f"  Kostnader uten areal: {len(mdp.get('costs_without_area', []))}")

    # 17. Kommune
    mup = patterns.get('municipality_patterns', {})
    if mup:
        p("KOSTNADER PER KOMMUNE")
        for x in mup.get('by_municipality', [])[:5]:
            print(f"  {x['municipality']}: {x['property_count']} eiendommer, total {x['total_costs']:,.0f} kr")

    # 18. Senter
    cep = patterns.get('center_patterns', {})
    if cep and cep.get('by_center'):
        p("KOSTNADER PER SENTER")
        for x in cep.get('by_center', [])[:5]:
            print(f"  {x['center_id']}: {x['property_count']} eiendommer, total {x['total_costs']:,.0f} kr")

    # 19. Transaksjonstetthet
    tdp = patterns.get('transaction_density_patterns', {})
    if tdp:
        p("TRANSAKSJONSTETTHET")
        low = tdp.get('low_density_few_transactions', [])[:3]
        high = tdp.get('high_density_many_transactions', [])[:3]
        if low:
            print(f"  Få transaksjoner, høye kostnader: {low}")
        if high:
            print(f"  Mange transaksjoner: {high}")

    # 20. Kategori-diversifikasjon
    cdp = patterns.get('category_diversification_patterns', {})
    if cdp:
        p("KATEGORI-DIVERSIFIKASJON")
        single = cdp.get('single_category_high_costs', [])[:5]
        if single:
            print("  Én kategori, høye kostnader:")
            for x in single:
                print(f"    {x['property'][:50]}: {x['category']}")

    print("\n✅ Ferdig\n")


async def main():
    if len(sys.argv) < 2:
        print("\nPattern Analysis Commands:")
        print("  python pattern_analyzer.py similar <property_name>")
        print("  python pattern_analyzer.py patterns")
        print("  python pattern_analyzer.py patterns extended")
        print("  python pattern_analyzer.py validate")
        return

    command = sys.argv[1].lower()
    arg2 = sys.argv[2].lower() if len(sys.argv) > 2 else ""

    if command == 'similar':
        if len(sys.argv) < 3:
            print("Usage: python pattern_analyzer.py similar <property_name>")
            return
        property_name = ' '.join(sys.argv[2:])
        await find_similar_properties(property_name)

    elif command == 'patterns':
        if arg2 == 'extended':
            await find_extended_patterns()
        else:
            await find_cost_patterns()

    elif command == 'validate':
        await validate_data()

    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())
