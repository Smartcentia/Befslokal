#!/usr/bin/env python3
"""
Audit script to identify properties with missing or incomplete data
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
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract


async def audit_incomplete_properties():
    """
    Identify properties with missing critical data
    """
    print("=" * 100)
    print("AUDIT: EIENDOMMER MED MANGLENDE INFORMASJON")
    print("=" * 100)
    
    async with SessionLocal() as db:
        # Get all properties with related units and contracts
        stmt = select(Property)
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        # Categories of issues
        issues = {
            'missing_address': [],
            'missing_postal_code': [],
            'missing_city': [],
            'missing_coordinates': [],
            'missing_area': [],
            'missing_building_year': [],
            'missing_energy_rating': [],
            'missing_units': [],
            'missing_contracts': [],
            'zero_area_units': [],
            'no_financial_data': [],
            'generic_name': [],
        }
        
        total_properties = len(properties)
        properties_with_issues = set()
        
        for prop in properties:
            property_issues = []
            
            # Check address
            if not prop.address or prop.address.strip() == '':
                issues['missing_address'].append(prop)
                property_issues.append('missing_address')
            
            # Check postal code
            if not prop.postal_code or prop.postal_code == '0000' or prop.postal_code.strip() == '':
                issues['missing_postal_code'].append(prop)
                property_issues.append('missing_postal_code')
            
            # Check city
            if not prop.city or prop.city == 'Ukjent' or prop.city.strip() == '':
                issues['missing_city'].append(prop)
                property_issues.append('missing_city')
            
            # Check coordinates
            if not prop.latitude or not prop.longitude:
                issues['missing_coordinates'].append(prop)
                property_issues.append('missing_coordinates')
            
            # Check area
            if not prop.total_area or prop.total_area == 0:
                issues['missing_area'].append(prop)
                property_issues.append('missing_area')
            
            # Check building year
            if not prop.construction_year or prop.construction_year == 0:
                issues['missing_building_year'].append(prop)
                property_issues.append('missing_building_year')
            
            # Check energy rating
            if not prop.energy_label or prop.energy_label.strip() == '':
                issues['missing_energy_rating'].append(prop)
                property_issues.append('missing_energy_rating')
            
            # Check units (load separately)
            units_stmt = select(Unit).where(Unit.property_id == prop.property_id)
            units_result = await db.execute(units_stmt)
            units = units_result.scalars().all()
            
            if not units or len(units) == 0:
                issues['missing_units'].append(prop)
                property_issues.append('missing_units')
            else:
                # Check for zero-area units
                for unit in units:
                    if not unit.size_m2 or unit.size_m2 == 0:
                        if prop not in issues['zero_area_units']:
                            issues['zero_area_units'].append(prop)
                            property_issues.append('zero_area_units')
                        break
            
            # Check contracts
            if units:
                has_active_contract = False
                for unit in units:
                    if unit.contract_id:
                        contract_stmt = select(Contract).where(Contract.contract_id == unit.contract_id)
                        contract_result = await db.execute(contract_stmt)
                        contract = contract_result.scalar_one_or_none()
                        if contract and contract.status == 'active':
                            has_active_contract = True
                            break
                
                if not has_active_contract:
                    issues['missing_contracts'].append(prop)
                    property_issues.append('missing_contracts')
            else:
                issues['missing_contracts'].append(prop)
                property_issues.append('missing_contracts')
            
            # Check financial data
            ext = prop.external_data or {}
            financials = ext.get('financials', {})
            has_expenses = financials.get('manual_expenses', [])
            has_total = financials.get('total_manual_expenses', 0)
            
            if not has_expenses and has_total == 0:
                issues['no_financial_data'].append(prop)
                property_issues.append('no_financial_data')
            
            # Check for generic/placeholder names
            generic_terms = ['ukjent', 'test', 'placeholder', 'temp', 'dummy']
            if any(term in prop.name.lower() for term in generic_terms):
                issues['generic_name'].append(prop)
                property_issues.append('generic_name')
            
            if property_issues:
                properties_with_issues.add(prop.property_id)
        
        # Print summary
        print(f"\n📊 Totalt {total_properties} eiendommer analysert")
        print(f"   Eiendommer med problemer: {len(properties_with_issues)} ({len(properties_with_issues)/total_properties*100:.1f}%)")
        
        print("\n" + "=" * 100)
        print("PROBLEMOVERSIKT")
        print("=" * 100)
        
        for issue_type, props in sorted(issues.items(), key=lambda x: -len(x[1])):
            if props:
                count = len(props)
                pct = (count / total_properties) * 100
                print(f"\n{issue_type.replace('_', ' ').title()}: {count} ({pct:.1f}%)")
        
        # Severity scoring
        print("\n" + "=" * 100)
        print("ALVORLIGHETSGRAD (Properties sortert etter antall mangler)")
        print("=" * 100)
        
        property_scores = defaultdict(lambda: {'issues': [], 'score': 0})
        
        severity_weights = {
            'missing_address': 10,
            'missing_postal_code': 8,
            'missing_city': 8,
            'missing_coordinates': 7,
            'missing_area': 9,
            'missing_building_year': 5,
            'missing_energy_rating': 3,
            'missing_units': 10,
            'missing_contracts': 6,
            'zero_area_units': 7,
            'no_financial_data': 4,
            'generic_name': 2,
        }
        
        for issue_type, props in issues.items():
            weight = severity_weights.get(issue_type, 5)
            for prop in props:
                property_scores[prop.property_id]['issues'].append(issue_type)
                property_scores[prop.property_id]['score'] += weight
                property_scores[prop.property_id]['name'] = prop.name
                property_scores[prop.property_id]['region'] = prop.region or 'Unknown'
        
        # Sort by severity
        sorted_properties = sorted(
            property_scores.items(),
            key=lambda x: (-x[1]['score'], x[1]['name'])
        )
        
        print(f"\nTopp 30 eiendommer med mest manglende data:\n")
        
        for prop_id, data in sorted_properties[:30]:
            print(f"📋 {data['name'][:60]}")
            print(f"   Region: {data['region']}")
            print(f"   Alvorlighetsgrad: {data['score']} poeng")
            print(f"   Mangler ({len(data['issues'])}): {', '.join(data['issues'][:5])}")
            if len(data['issues']) > 5:
                print(f"      ... og {len(data['issues']) - 5} flere")
            print()
        
        # Export detailed report
        export_dir = os.path.join(os.path.dirname(__file__), '..')
        with open(os.path.join(export_dir, 'incomplete_properties_report.txt'), 'w', encoding='utf-8') as f:
            f.write("RAPPORT: EIENDOMMER MED MANGLENDE DATA\n")
            f.write("=" * 100 + "\n\n")
            
            f.write(f"Totalt eiendommer: {total_properties}\n")
            f.write(f"Eiendommer med problemer: {len(properties_with_issues)}\n\n")
            
            f.write("PROBLEMOVERSIKT:\n")
            f.write("-" * 100 + "\n")
            for issue_type, props in sorted(issues.items(), key=lambda x: -len(x[1])):
                if props:
                    f.write(f"\n{issue_type.replace('_', ' ').title()}: {len(props)}\n")
                    for prop in props[:10]:  # First 10 of each type
                        f.write(f"  - {prop.name}\n")
                    if len(props) > 10:
                        f.write(f"  ... og {len(props) - 10} flere\n")
            
            f.write(f"\n\nALLE EIENDOMMER SORTERT ETTER ALVORLIGHETSGRAD:\n")
            f.write("-" * 100 + "\n")
            for prop_id, data in sorted_properties:
                f.write(f"\n{data['name']}\n")
                f.write(f"  Region: {data['region']}\n")
                f.write(f"  Score: {data['score']}\n")
                f.write(f"  Mangler: {', '.join(data['issues'])}\n")
        
        print(f"✅ Detaljert rapport eksportert til: incomplete_properties_report.txt")


if __name__ == "__main__":
    asyncio.run(audit_incomplete_properties())
