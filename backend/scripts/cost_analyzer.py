#!/usr/bin/env python3
"""
EXPERT PROPERTY COST ANALYZER
==============================
Intelligent script for finding, comparing, and analyzing property costs.

Usage examples:
  python cost_analyzer.py search "Alta"
  python cost_analyzer.py compare "Bodø" "Alta" "Tromsø"
  python cost_analyzer.py details "Bufetathus Kristiansand"
  python cost_analyzer.py region "01 - Nord"
  python cost_analyzer.py anomalies
  python cost_analyzer.py patterns    - Utvidede kostnadsmønstre (regional, leverandør, cluster, etc.)
  python cost_analyzer.py top 10 costs
  python cost_analyzer.py top 10 rent
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
from app.domains.core.utils.region_mapping import get_operational_region


class CostAnalyzer:
    def __init__(self):
        self.properties = []
        self.property_data = {}
        self.regional_stats = {}
    
    async def load_data(self):
        """Load all property and cost data"""
        print("📊 Loading data...")
        
        async with SessionLocal() as db:
            # Get all properties
            stmt_prop = select(Property)
            result_prop = await db.execute(stmt_prop)
            self.properties = result_prop.scalars().all()
            
            # Get all active contracts
            stmt_contract = (
                select(Contract)
                .where(Contract.status == 'active')
                .options(joinedload(Contract.unit).joinedload(Unit.property))
            )
            result_contract = await db.execute(stmt_contract)
            contracts = result_contract.scalars().all()
            
            # Build property -> contract mapping
            property_contracts = {}
            for contract in contracts:
                if contract.unit and contract.unit.property:
                    prop_id = contract.unit.property.property_id
                    if prop_id not in property_contracts:
                        property_contracts[prop_id] = []
                    property_contracts[prop_id].append(contract)
            
            # Build comprehensive data for each property
            for prop in self.properties:
                prop_id = prop.property_id
                
                # Get rent data
                total_rent = 0
                contracts_list = []
                if prop_id in property_contracts:
                    for contract in property_contracts[prop_id]:
                        amount_data = contract.amount if isinstance(contract.amount, dict) else {}
                        rent = amount_data.get('amount_per_year', 0)
                        try:
                            rent = float(rent) if rent else 0
                        except:
                            rent = 0
                        total_rent += rent
                        contracts_list.append({
                            'rent': rent,
                            'start': contract.start_date,
                            'end': contract.end_date
                        })
                
                # Get cost data
                ext = prop.external_data or {}
                expenses = ext.get('financials', {}).get('manual_expenses', [])
                
                total_costs = 0
                cost_by_category = defaultdict(float)
                cost_by_provider = defaultdict(float)
                
                for exp in expenses:
                    try:
                        amount = float(exp.get('amount', 0) or 0)
                        total_costs += amount
                        category = exp.get('type', 'Ukjent')
                        provider = exp.get('provider', 'Ukjent')
                        cost_by_category[category] += amount
                        cost_by_provider[provider] += amount
                    except:
                        pass
                
                # Store comprehensive data
                # Normalize region using the centralized utility
                normalized_region = get_operational_region(prop.region or 'Unknown')
                
                self.property_data[prop.name.lower()] = {
                    'property': prop,
                    'name': prop.name,
                    'region': normalized_region,
                    'address': prop.address or '',
                    'rent': total_rent,
                    'costs': total_costs,
                    'total': total_rent + total_costs,
                    'num_contracts': len(contracts_list),
                    'num_expenses': len(expenses),
                    'contracts': contracts_list,
                    'expenses': expenses,
                    'cost_by_category': dict(cost_by_category),
                    'cost_by_provider': dict(cost_by_provider)
                }
            
            # Calculate regional statistics
            for data in self.property_data.values():
                region = data['region']
                if region not in self.regional_stats:
                    self.regional_stats[region] = {
                        'properties': [],
                        'total_rent': 0,
                        'total_costs': 0,
                        'count': 0
                    }
                
                self.regional_stats[region]['properties'].append(data)
                self.regional_stats[region]['total_rent'] += data['rent']
                self.regional_stats[region]['total_costs'] += data['costs']
                self.regional_stats[region]['count'] += 1
            
            # Calculate averages
            for region, stats in self.regional_stats.items():
                count = stats['count']
                stats['avg_rent'] = stats['total_rent'] / count if count > 0 else 0
                stats['avg_costs'] = stats['total_costs'] / count if count > 0 else 0
        
        print(f"✅ Loaded {len(self.properties)} properties")
    
    def search(self, query):
        """Search for properties by name"""
        query = query.lower()
        matches = []
        
        for key, data in self.property_data.items():
            if query in key:
                matches.append(data)
        
        return matches
    
    def get_property(self, name):
        """Get exact property by name (case-insensitive)"""
        name_lower = name.lower()
        
        # Try exact match first
        if name_lower in self.property_data:
            return self.property_data[name_lower]
        
        # Try partial match
        matches = self.search(name)
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            print(f"\n⚠️  Multiple matches found for '{name}':")
            for i, match in enumerate(matches, 1):
                print(f"   {i}. {match['name']}")
            return None
        else:
            print(f"\n❌ No property found matching '{name}'")
            return None
    
    def print_property_details(self, data):
        """Print detailed information about a property"""
        print("\n" + "=" * 80)
        print(f"PROPERTY: {data['name']}")
        print("=" * 80)
        
        print(f"\n📍 Basic Info:")
        print(f"   Region: {data['region']}")
        print(f"   Address: {data['address']}")
        
        print(f"\n💰 Financial Summary:")
        print(f"   Årlig husleie:    {data['rent']:>15,.0f} kr")
        print(f"   Årlige kostnader: {data['costs']:>15,.0f} kr")
        print(f"   Total:            {data['total']:>15,.0f} kr")
        
        print(f"\n📊 Data Status:")
        print(f"   Kontrakter: {data['num_contracts']}")
        print(f"   Kostnadstransaksjoner: {data['num_expenses']}")
        
        if data['cost_by_category']:
            print(f"\n📋 Kostnader per Kategori:")
            sorted_cats = sorted(data['cost_by_category'].items(), key=lambda x: -x[1])
            for cat, amount in sorted_cats[:10]:
                pct = (amount / data['costs'] * 100) if data['costs'] > 0 else 0
                print(f"   {cat[:50]:<50} {amount:>12,.0f} kr ({pct:>5.1f}%)")
            if len(sorted_cats) > 10:
                print(f"   ... og {len(sorted_cats) - 10} flere kategorier")
        
        if data['cost_by_provider']:
            print(f"\n🏢 Største Leverandører:")
            sorted_provs = sorted(data['cost_by_provider'].items(), key=lambda x: -x[1])
            for prov, amount in sorted_provs[:5]:
                print(f"   {prov[:50]:<50} {amount:>12,.0f} kr")
        
        # Compare to regional average
        region = data['region']
        if region in self.regional_stats:
            avg_costs = self.regional_stats[region]['avg_costs']
            if avg_costs > 0:
                diff = data['costs'] - avg_costs
                pct_diff = (diff / avg_costs) * 100
                print(f"\n📈 Sammenligning med {region} gjennomsnitt:")
                print(f"   Regionalt snitt: {avg_costs:>12,.0f} kr")
                print(f"   Denne eiendom: {data['costs']:>14,.0f} kr")
                if diff > 0:
                    print(f"   Differanse: +{diff:,.0f} kr ({pct_diff:+.1f}%)")
                else:
                    print(f"   Differanse: {diff:,.0f} kr ({pct_diff:+.1f}%)")
    
    def compare_properties(self, names):
        """Compare multiple properties"""
        properties_data = []
        
        for name in names:
            data = self.get_property(name)
            if data:
                properties_data.append(data)
        
        if len(properties_data) < 2:
            print("\n❌ Need at least 2 properties to compare")
            return
        
        print("\n" + "=" * 80)
        print("PROPERTY COMPARISON")
        print("=" * 80)
        
        # Table header
        print(f"\n{'Property':<40} {'Rent':>15} {'Costs':>15} {'Total':>15}")
        print("-" * 87)
        
        for data in properties_data:
            print(f"{data['name'][:38]:<40} {data['rent']:>15,.0f} {data['costs']:>15,.0f} {data['total']:>15,.0f}")
        
        # Category comparison
        print(f"\n📋 Cost Categories Comparison:")
        all_categories = set()
        for data in properties_data:
            all_categories.update(data['cost_by_category'].keys())
        
        # Print top 10 categories
        for cat in sorted(all_categories)[:10]:
            print(f"\n   {cat}:")
            for data in properties_data:
                amount = data['cost_by_category'].get(cat, 0)
                if amount > 0:
                    print(f"      {data['name'][:35]:<35} {amount:>12,.0f} kr")
    
    def show_regional_stats(self, region):
        """Show statistics for a region"""
        if region not in self.regional_stats:
            print(f"\n❌ Region '{region}' not found")
            return
        
        stats = self.regional_stats[region]
        
        print("\n" + "=" * 80)
        print(f"REGIONAL STATISTICS: {region}")
        print("=" * 80)
        
        print(f"\n📊 Overview:")
        print(f"   Properties: {stats['count']}")
        print(f"   Total rent: {stats['total_rent']:,.0f} kr/år")
        print(f"   Total costs: {stats['total_costs']:,.0f} kr/år")
        print(f"   Average rent: {stats['avg_rent']:,.0f} kr/år")
        print(f"   Average costs: {stats['avg_costs']:,.0f} kr/år")
        
        print(f"\n🏛️ Top 10 Properties by Total Cost:")
        sorted_props = sorted(stats['properties'], key=lambda x: -(x['rent'] + x['costs']))
        for i, data in enumerate(sorted_props[:10], 1):
            print(f"   {i:2}. {data['name'][:50]:<50} {data['total']:>12,.0f} kr")
    
    def find_anomalies(self):
        """Find properties with unusual cost patterns"""
        print("\n" + "=" * 80)
        print("COST ANOMALIES")
        print("=" * 80)
        
        # High rent, no costs
        print(f"\n🚨 High Rent, No Costs (Top 10):")
        high_rent_no_costs = [
            d for d in self.property_data.values() 
            if d['rent'] > 1_000_000 and d['costs'] == 0
        ]
        sorted_high = sorted(high_rent_no_costs, key=lambda x: -x['rent'])
        for data in sorted_high[:10]:
            print(f"   {data['name'][:50]:<50} {data['rent']:>12,.0f} kr rent")
        
        # High costs, no rent
        print(f"\n🚨 High Costs, No Rent (Top 10):")
        high_costs_no_rent = [
            d for d in self.property_data.values() 
            if d['costs'] > 1_000_000 and d['rent'] == 0
        ]
        sorted_costs = sorted(high_costs_no_rent, key=lambda x: -x['costs'])
        for data in sorted_costs[:10]:
            print(f"   {data['name'][:50]:<50} {data['costs']:>12,.0f} kr costs")
        
        # Extreme cost-to-rent ratios
        print(f"\n📊 Extreme Cost-to-Rent Ratios:")
        properties_with_both = [
            d for d in self.property_data.values() 
            if d['rent'] > 0 and d['costs'] > 0
        ]
        for data in properties_with_both:
            ratio = data['costs'] / data['rent']
            data['ratio'] = ratio
        
        high_ratios = sorted(properties_with_both, key=lambda x: -x['ratio'])[:5]
        print(f"\n   Highest cost-to-rent ratios:")
        for data in high_ratios:
            print(f"   {data['name'][:40]:<40} Ratio: {data['ratio']:.2f} (costs {data['ratio']*100:.0f}% of rent)")
    
    def show_top(self, n, by='total'):
        """Show top N properties by rent, costs, or total"""
        print("\n" + "=" * 80)
        if by == 'rent':
            print(f"TOP {n} PROPERTIES BY RENT")
            sorted_props = sorted(self.property_data.values(), key=lambda x: -x['rent'])
        elif by == 'costs':
            print(f"TOP {n} PROPERTIES BY COSTS")
            sorted_props = sorted(self.property_data.values(), key=lambda x: -x['costs'])
        else:
            print(f"TOP {n} PROPERTIES BY TOTAL (RENT + COSTS)")
            sorted_props = sorted(self.property_data.values(), key=lambda x: -x['total'])
        print("=" * 80)
        
        print(f"\n{'#':<4} {'Property':<45} {'Rent':>15} {'Costs':>15} {'Total':>15}")
        print("-" * 97)
        
        for i, data in enumerate(sorted_props[:n], 1):
            print(f"{i:<4} {data['name'][:43]:<45} {data['rent']:>15,.0f} {data['costs']:>15,.0f} {data['total']:>15,.0f}")


async def main():
    analyzer = CostAnalyzer()
    await analyzer.load_data()
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python cost_analyzer.py search <query>")
        print("  python cost_analyzer.py details <property_name>")
        print("  python cost_analyzer.py compare <prop1> <prop2> [prop3...]")
        print("  python cost_analyzer.py region <region_name>")
        print("  python cost_analyzer.py anomalies")
        print("  python cost_analyzer.py patterns")
        print("  python cost_analyzer.py top <n> [rent|costs|total]")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'search':
        if len(sys.argv) < 3:
            print("Usage: python cost_analyzer.py search <query>")
            return
        query = ' '.join(sys.argv[2:])
        matches = analyzer.search(query)
        print(f"\n🔍 Found {len(matches)} matches for '{query}':")
        for data in matches:
            status = "✅" if data['rent'] > 0 and data['costs'] > 0 else "⚠️"
            print(f"   {status} {data['name']} - Rent: {data['rent']:,.0f} kr, Costs: {data['costs']:,.0f} kr")
    
    elif command == 'details':
        if len(sys.argv) < 3:
            print("Usage: python cost_analyzer.py details <property_name>")
            return
        name = ' '.join(sys.argv[2:])
        data = analyzer.get_property(name)
        if data:
            analyzer.print_property_details(data)
    
    elif command == 'compare':
        if len(sys.argv) < 4:
            print("Usage: python cost_analyzer.py compare <prop1> <prop2> [prop3...]")
            return
        names = sys.argv[2:]
        analyzer.compare_properties(names)
    
    elif command == 'region':
        if len(sys.argv) < 3:
            print("Usage: python cost_analyzer.py region <region_name>")
            return
        region = ' '.join(sys.argv[2:])
        analyzer.show_regional_stats(region)
    
    elif command == 'anomalies':
        analyzer.find_anomalies()

    elif command == 'patterns':
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from pattern_analyzer import find_extended_patterns
        await find_extended_patterns()

    elif command == 'top':
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        by = sys.argv[3] if len(sys.argv) > 3 else 'total'
        analyzer.show_top(n, by)
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    asyncio.run(main())
