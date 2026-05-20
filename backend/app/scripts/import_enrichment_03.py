
import asyncio
import sys
import os
import re
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from difflib import SequenceMatcher
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Load env before imports that might use it
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
# Import related models to populate registry
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.user import User
from app.domains.core.models.party import Party

BUREAUS = [
    "Barnevernsinstitusjoner",
    "Familieverntjeneste",
    "Fosterhjem",
    "Hjelpetiltak i hjemmet",
    "Inntak",
    "Regionale fellesfunksjoner",
    "Sentre for foreldre og barn",
    "Senter for foreldre og barn",
    "Omsorgssentre for mindreårige asylsøkere",
    "Adopsjon",
    "Fosterhjemstjenesten",
    "Statlige institusjoner",
    "Omsorgssenter for enslige mindreårige asylsøkere"
]

EXPENSE_CATEGORIES = [
    "Renhold lokaler",
    "Fellesutgifter andre utleiere",
    "Leie lokaler andre utleiere",
    "Strøm og oppvarming",
    "Renovasjon, vann, avløp o.l.",
    "Leie lokaler fra Statsbygg",
    "Fellesutgifter (BAD) Statsbygg",
    "Fellesutgifter Statsbygg - indre vedlikehold",
    "Vaktmestertjenester",
    "Vakthold lokaler",
    "Annen kostnad lokaler",
    "Reparasjon og vedlikehold leide lokaler",
    "Oppgradering og påkostning leide lokaler - under kr 50 000",
    "Leie parkeringsplass",
    "Fellesutgifter",
    "Reparasjon og vedlikehold av anlegg, også serviceavtaler",
    "Leie av lager/naust/garsjer og lignende"
]

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def parse_line(line: str) -> Optional[Dict[str, Any]]:
    line = line.strip()
    if not line: return None

    # Match ID
    # Usually starts with Region code space Region Name space ID
    # Example: 2 Region Øst 204416 ...
    match = re.search(r'Region\s+[\wØæåøÆÅ]+\s+(\d{5,6})\s+', line)
    if not match:
        return None
    
    center_id = match.group(1)
    
    # Locate bureau to split
    # Sort by length descending to match longest possible bureau name first
    bureau_found = None
    sorted_bureaus = sorted(BUREAUS, key=len, reverse=True)
    for b in sorted_bureaus:
        if b in line:
            bureau_found = b
            # We want to find the first occurrence of this bureau after the ID
            break
            
    if not bureau_found:
        return None
        
    id_pos = line.find(center_id)
    id_end = id_pos + len(center_id)
    bureau_start = line.find(bureau_found, id_end)
    
    # Property identifier is between ID and Bureau
    # In 03.txt this often includes secondary ID and Address
    property_key = line[id_end:bureau_start].strip()
    
    # Rest is after Bureau
    rest = line[bureau_start + len(bureau_found):].strip()
    
    # Amount is at the end
    # Handles 1250, 113721,2, -92,69, 1423.27
    amount_match = re.search(r'(-?[\d\s,.]+)$', rest)
    if not amount_match:
        return None
        
    amount_str = amount_match.group(1).strip()
    # Replace comma decimal with dot, then remove spaces
    amount_clean = amount_str.replace(',', '.')
    amount_clean = re.sub(r'[^\d.-]', '', amount_clean)
    
    try:
        amount = float(amount_clean)
    except:
        amount = 0.0
        
    rest_no_amount = rest[:amount_match.start()].strip()
    
    # Find Category
    category_found = "Annet"
    provider = rest_no_amount
    
    # Try to extract category if it matches known ones
    for cat in sorted(EXPENSE_CATEGORIES, key=len, reverse=True):
        if cat in rest_no_amount:
            category_found = cat
            provider = rest_no_amount.replace(cat, "").strip()
            break
            
    if not provider: provider = "Ukjent"

    return {
        "property_key": property_key,
        "category": category_found,
        "provider": provider,
        "amount": amount
    }

async def update_database(file_path: str):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    parsed_items = []
    for line in lines:
        p = parse_line(line)
        if p:
            parsed_items.append(p)
            
    print(f"Parsed {len(parsed_items)} transactions from file.")

    # Group by property
    by_property = {}
    for item in parsed_items:
        prop_key = item['property_key']
        if prop_key not in by_property:
            by_property[prop_key] = []
        by_property[prop_key].append(item)
        
    async with SessionLocal() as db:
        # Load properties
        result = await db.execute(select(Property))
        all_properties = result.scalars().all()
        
        updated_count = 0
        matches_found = []

        for raw_key, transactions in by_property.items():
            clean_key = raw_key.lower().strip()
            
            best_prop = None
            best_score = 0.0
            
            # Extract potential address parts from the raw_key
            # Often looks like: 2050182 Korpåsen 172, 1386 Asker
            addr_match = re.search(r'\d{7}\s+(.+)', raw_key)
            if addr_match:
                extracted_addr = addr_match.group(1).lower()
            else:
                extracted_addr = clean_key

            for p in all_properties:
                score = similar(clean_key, p.name.lower())
                addr_score = similar(extracted_addr, (p.address or "").lower())
                max_score = max(score, addr_score)
                
                if max_score > best_score:
                    best_score = max_score
                    best_prop = p
            
            # Substring fallback for specific names or addresses
            if best_score < 0.65:
                 for p in all_properties:
                     if clean_key in p.name.lower() or (p.address and clean_key in p.address.lower()) or (p.address and p.address.lower() in clean_key):
                         best_prop = p
                         best_score = 0.85 # Confidence via substring
                         break

            if best_score > 0.65:
                # Enrich external_data
                if not best_prop.external_data:
                    best_prop.external_data = {}
                
                fin = best_prop.external_data.get('financials', {})
                if not isinstance(fin, dict):
                    fin = {}
                
                existing_expenses = fin.get('manual_expenses', [])
                
                new_expenses = []
                total_new = 0.0
                for t in transactions:
                    new_expenses.append({
                        "type": t['category'],
                        "provider": t['provider'],
                        "amount": t['amount'],
                        "amount_parsed": t['amount'],
                        "date": "2026-Q1",
                        "source": "docs/03.txt"
                    })
                    total_new += t['amount']
                
                # Enrich
                fin['manual_expenses'] = existing_expenses + new_expenses
                fin['total_manual_expenses'] = fin.get('total_manual_expenses', 0.0) + total_new
                fin['data_source'] = 'multi_source_enrichment_2026'
                
                best_prop.external_data['financials'] = fin
                
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(best_prop, "external_data")
                db.add(best_prop)
                updated_count += 1
                
        await db.commit()
        print(f"Import Summary for 03.txt:")
        print(f"- Unique Property keys identified: {len(by_property)}")
        print(f"- Properties matched and updated: {updated_count}")
        print(f"- Total transactions imported: {len(parsed_items)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_enrichment_03.py <file_path>")
    else:
        file_path = sys.argv[1]
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.getcwd(), file_path)
        asyncio.run(update_database(file_path))
