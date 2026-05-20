
import asyncio
import sys
import os
import re
from typing import List, Dict, Optional
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from difflib import SequenceMatcher
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
# Import related models to populate registry

try:
    from app.domains.hms.models.risk import RiskAssessment
    from app.domains.hms.models.internal_control import InternalControlCase
    from app.domains.core.models.user import User
except ImportError:
    pass # Should work if paths are correct

KNOWN_EXPENSE_TYPES = {
    "Husleie", "Felleskostnader", "Strøm", "Renhold", 
    "Felleskost (BAD)", "Indre vedlikehold", "Vakthold", 
    "Vaktmester", "Leie", "Renovasjon", "Prosjekt", 
    "Prosjekt/Bygg", "Prosjekt (Rehab)", "Renovasjon"
}

SKIP_LINES = {
    "Eiendom / Adresse", "Type Utgift", "Leverandør / Mottaker", 
    "Beløp (Eks.)", "Beløp (Eks. fra bilag)", "--------------------------------------------------------------------------------",
    "Kostnadstype", "Leverandør / Detaljer", "Kilde", ","
}

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def parse_file(filepath: str) -> Dict[str, List[Dict]]:
    data = {}
    current_property = None
    
    with open(filepath, 'r') as f:
        lines = [l.strip() for l in f if l.strip()]

    started = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip preamble until first region
        if not started:
            if "1. Region" in line:
                started = True
            else:
                i += 1
                continue
                
        # Skip headers / region markers
        # Robust check for "1. Region", "2. Region", etc. or "Region / Bruk"
        if "Region" in line and (line[0].isdigit() or line.startswith("Region")):
            i += 1
            continue
            
        if line in SKIP_LINES or "----------------" in line:
            i += 1
            continue
            
        # Check if it is description text (long lines, no numbers, etc) - simple heuristic
        if line.startswith("Mye aktivitet") or line.startswith("Store beløp") or line.startswith("Her er en") or line.startswith("Tabellen er") or line.startswith("Oppsummering"):
             i += 1
             continue

        # Logic:
        # If line is a Known Expense Type -> Parse Triplet
        # Else -> It is a Property Name -> Start new Property
        
        # Clean line for comparison
        clean_line = line.replace(":", "").strip()
        
        if clean_line in KNOWN_EXPENSE_TYPES:
            if current_property is None:
                # print(f"WARNING: Expense found without property: {line}")
                i += 1
                continue
                
            expense_type = clean_line
            # Next line is Provider
            if i + 1 < len(lines):
                provider = lines[i+1]
            else:
                provider = "Unknown"
                
            # Next line is Amount
            if i + 2 < len(lines):
                amount = lines[i+2]
            else:
                amount = "Unknown"
                
            data[current_property].append({
                "type": expense_type,
                "provider": provider,
                "amount": amount
            })
            
            i += 3 # Consumed Type, Provider, Amount
        else:
            # It is a Property Name
            current_property = line
            if current_property not in data:
                data[current_property] = []
            i += 1
            
    return data

async def update_database(parsed_data: Dict[str, List[Dict]]):
    async with SessionLocal() as db:
        print("Connected to DB, fetching properties...")
        # Fetch all properties
        result = await db.execute(select(Property))
        all_props = result.scalars().all()
        
        matches_found = 0
        
        print("\n--- Starting Import ---")
        
        for raw_name, expenses in parsed_data.items():
            # Clean raw name
            clean_name = raw_name.split('(')[0].strip().lower()
            
            best_prop = None
            best_score = 0.0
            
            for p in all_props:
                # Check Name
                p_name_clean = (p.name or "").lower()
                score_name = similar(clean_name, p_name_clean)
                
                # Check Address
                p_addr_clean = (p.address or "").lower()
                score_addr = similar(clean_name, p_addr_clean)
                
                current_max = max(score_name, score_addr)
                
                if current_max > best_score:
                    best_score = current_max
                    best_prop = p

            # Threshold for difflib (0.0 to 1.0)
            # 0.8 is roughly equivalent to 80% fuzzy match
            if best_score > 0.7:
                print(f"MATCH: '{raw_name}' -> '{best_prop.name or 'Unknown'}' (Score: {best_score:.2f})")
                
                # Update External Data
                if not best_prop.external_data:
                    best_prop.external_data = {}
                
                fin_data = best_prop.external_data.get('financials', {})
                if not isinstance(fin_data, dict):
                    fin_data = {}
                    
                # Calculate total
                total_manual = 0.0
                for exp in expenses:
                    try:
                        # Clean amount string: "1 036 510,-" -> 1036510.0
                        # Remove 'kr', ',-', spaces
                        raw = exp['amount']
                        # Take first part if slash exists
                        raw = raw.split('/')[0]
                        # Remove non-numeric chars except dot/comma (replace comma with dot if decimal, but here usually thousands sep is space and decimal is comma)
                        # Norwegian format: 1.000,00 or 1 000,00. 
                        # Simply removing spaces and replacing , with . might work if it's standard.
                        # However, typical "10 000,-" means integer 10000.
                        # Let's try simple digit extraction if integers.
                        
                        clean = re.sub(r'[^\d]', '', raw)
                        if clean:
                            val = float(clean)
                            if val > 0:
                                total_manual += val
                                exp['amount_parsed'] = val # Store parsed value
                    except Exception as e:
                        print(f"Failed to parse amount: {exp['amount']} ({e})")

                fin_data['manual_expenses'] = expenses
                fin_data['total_manual_expenses'] = total_manual
                fin_data['data_source'] = 'manual_text_import_jan_2026'
                
                best_prop.external_data['financials'] = fin_data
                
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(best_prop, "external_data")
                
                db.add(best_prop)
                matches_found += 1
            else:
                 # Fallback: Try simple substring match for high confidence
                 substring_match = None
                 for p in all_props:
                     if clean_name in (p.name or "").lower() or (p.address and clean_name in p.address.lower()):
                         substring_match = p
                         break
                 
                 if substring_match:
                     print(f"MATCH (Substring): '{raw_name}' -> '{substring_match.name}'")
                     best_prop = substring_match
                     
                     if not best_prop.external_data:
                        best_prop.external_data = {}
                
                     fin_data = best_prop.external_data.get('financials', {})
                     if not isinstance(fin_data, dict):
                        fin_data = {}

                     # Calculate total
                     total_manual = 0.0
                     for exp in expenses:
                        try:
                            raw = exp['amount']
                            raw = raw.split('/')[0]
                            clean = re.sub(r'[^\d]', '', raw)
                            if clean:
                                val = float(clean)
                                if val > 0:
                                    total_manual += val
                                    exp['amount_parsed'] = val
                        except Exception:
                            pass
                        
                     fin_data['manual_expenses'] = expenses
                     fin_data['total_manual_expenses'] = total_manual
                     fin_data['data_source'] = 'manual_text_import_jan_2026'
                     best_prop.external_data['financials'] = fin_data
                     
                     from sqlalchemy.orm.attributes import flag_modified
                     flag_modified(best_prop, "external_data")
                     
                     db.add(best_prop)
                     matches_found += 1
                 else:
                    print(f"NO MATCH: '{raw_name}' (Best Score: {best_score:.2f})")

        await db.commit()
        print(f"\nSummary: Updated {matches_found} / {len(parsed_data)} properties.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to text file")
    args = parser.parse_args()
    
    data = parse_file(args.file)
    
    # Print sample to verify parse
    print(f"Parsed {len(data)} properties.")
    # sample key
    if data:
        k = list(data.keys())[0]
        print(f"Sample: {k} -> {data[k]}")
        
    asyncio.run(update_database(data))
