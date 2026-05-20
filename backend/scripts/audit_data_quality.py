
import asyncio
import sys
import os
import re
from collections import defaultdict
from typing import List, Dict, Any
from sqlalchemy import select
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Load env
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal

# Import models
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.user import User
from app.domains.core.models.party import Party
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

# Simplified region check (loose string matching, se docs/REGION_STANDARD.md)
REGION_KEYWORDS = {
    'Midt-Norge': ['midt', 'trøndelag', 'møre'],
    'Øst': ['øst', 'oslo', 'viken', 'innlandet', 'akershus'],
    'Vest': ['vest', 'bergen', 'rogaland'],
    'Sør': ['sør', 'agder', 'telemark', 'vestfold'],
    'Nord': ['nord', 'troms', 'finnmark', 'nordland'],
    'Bufdir': ['bufdir'],
}

async def audit_data():
    print("Starting Comprehensive Data Quality Audit...")
    print("-" * 60)
    
    async with SessionLocal() as db:
        # Fetch all properties with external data
        stmt = select(Property).where(Property.external_data.is_not(None))
        result = await db.execute(stmt)
        properties = result.scalars().all()
        
        # Metrics
        total_properties_checked = 0
        total_transactions_checked = 0
        
        # Issues
        duplicate_transactions = [] # (prop_id, transaction_signature)
        regional_mismatches = []    # (prop_id, source_file, prop_region)
        outliers_high = []          # > 1M
        outliers_negative = []      # < 0
        unknown_providers = 0
        
        # Transaction Signature Tracker (Global)
        # Signature: (amount, provider, type, date) -> list of (prop_id, source)
        global_transaction_map = defaultdict(list)
        
        for prop in properties:
            ext = prop.external_data or {}
            fin = ext.get('financials', {})
            expenses = fin.get('manual_expenses', [])
            
            if not expenses:
                continue
                
            total_properties_checked += 1
            
            seen_in_property = set()
            
            for exp in expenses:
                total_transactions_checked += 1
                
                try:
                    amount_raw = exp.get('amount', 0)
                    amount = float(amount_raw) if amount_raw is not None else 0.0
                except (ValueError, TypeError):
                    amount = 0.0

                provider = exp.get('provider', 'Ukjent')
                category = exp.get('type', 'Ukjent')
                source = exp.get('source', 'Unknown')
                date = exp.get('date', 'Unknown')
                
                # 1. Global Duplicate Check
                sig = (amount, provider, category, date)
                
                # Check internal double-counting
                if sig in seen_in_property:
                    # Only flag if amount is non-trivial/not generic
                    if amount != 0: 
                        duplicate_transactions.append({
                            "type": "Internal Duplicate",
                            "prop_name": prop.name,
                            "signature": str(sig),
                            "source": source
                        })
                seen_in_property.add(sig)
                
                global_transaction_map[sig].append((prop.property_id, prop.name, source))
                
                # 2. Regional Integrity
                # Map source file to expected region
                # Extract filename from source "docs/14.txt"
                match = re.search(r'docs/\d+\.txt', source)
                if match:
                    filename = match.group(0)
                    expected_initial = FILE_REGION_MAP.get(filename)
                    if expected_initial:
                        # Normalize prop region
                        prop_reg_str = str(prop.region).lower()
                        
                        # Loose check
                        # If "03 - Sør" matches "03" in property region code or keyword
                        expected_key_parts = expected_initial.split(' - ')
                        region_code = expected_key_parts[0]
                        region_name = expected_key_parts[1].lower() if len(expected_key_parts) > 1 else ""
                        
                        # We expect prop.region (e.g. "03") to match code
                        # However, sometimes prop.region is just "03" or "Region Sør"
                        
                        is_match = False
                        if region_code in prop_reg_str:
                            is_match = True
                        elif region_name and region_name in prop_reg_str:
                            is_match = True
                        
                        # Special case: 10.txt might be generic?
                        if not is_match:
                             regional_mismatches.append({
                                 "prop_name": prop.name,
                                 "prop_region": prop.region,
                                 "source_file": filename,
                                 "expected_region": expected_initial
                             })
                
                # 3. Financial Anomalies
                if amount > 1000000:
                    outliers_high.append({
                        "prop_name": prop.name,
                        "amount": amount,
                        "provider": provider,
                        "source": source
                    })
                
                if amount < 0:
                     outliers_negative.append({
                        "prop_name": prop.name,
                        "amount": amount,
                        "provider": provider,
                        "source": source
                    })
                    
                # 4. Data Completeness
                if provider.lower() in ['ukjent', 'unknown', '']:
                    unknown_providers += 1

        # Analyze Global Duplicates (Cross-Property)
        cross_property_duplicates = []
        for sig, occurrences in global_transaction_map.items():
            if len(occurrences) > 1:
                # Check if they are different properties
                props = set(o[0] for o in occurrences)
                if len(props) > 1:
                     cross_property_duplicates.append({
                         "signature": str(sig),
                         "count": len(occurrences),
                         "files": list(set(o[2] for o in occurrences)),
                         "props": list(set(o[1] for o in occurrences))
                     })

        print(f"AUDIT COMPLETE.")
        print(f"Properties Checked: {total_properties_checked}")
        print(f"Transactions Checked: {total_transactions_checked}")
        print("-" * 60)
        
        print(f"1. DUPLICATES")
        print(f"   - Internal (same property) duplicates found: {len(duplicate_transactions)}")
        if duplicate_transactions:
            print("     Sample: " + str(duplicate_transactions[:3]))
        print(f"   - Cross-Property duplicates found: {len(cross_property_duplicates)}")
        if cross_property_duplicates:
             # Sort by count
             cross_property_duplicates.sort(key=lambda x: x['count'], reverse=True)
             print("     Top 5 suspicious cross-duplicates:")
             for d in cross_property_duplicates[:5]:
                 print(f"       {d['signature']} -> {d['count']} times in {len(d['props'])} properties")
        
        print("\n2. REGIONAL INTEGRITY")
        print(f"   - Mismatches found: {len(regional_mismatches)}")
        if regional_mismatches:
            print("     Sample:")
            for m in regional_mismatches[:5]:
                print(f"       {m['prop_name']} (Reg: {m['prop_region']}) <-> Source: {m['source_file']} (Exp: {m['expected_region']})")

        print("\n3. FINANCIAL ANOMALIES")
        print(f"   - Amounts > 1,000,000 NOK: {len(outliers_high)}")
        if outliers_high:
            for o in outliers_high[:3]:
                print(f"       {o['prop_name']}: {o['amount']} ({o['provider']})")
                
        print(f"   - Negative Amounts (Credit Notes/Corrections): {len(outliers_negative)}")
        
        print("\n4. DATA COMPLETENESS")
        print(f"   - 'Ukjent' Providers: {unknown_providers} ({(unknown_providers/total_transactions_checked)*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(audit_data())
