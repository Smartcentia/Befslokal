
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
    "Omsorgssentre for mindreårige asylsøkere",
    "Adopsjon",
    "Fosterhjemstjenesten",
    "Statlige institusjoner",
    "Administrasjon",
    "Enhet for inntak",
    "Prosjektering og utvikling av eiendom/bygg",
    "Større anskaffelser",
    "Selvassuranse",
    "Tverrfaglig helsekartlegging av barn i barnevernet"
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
    "Fast bygningsinventar over kr 50 000",
    "Leie parkeringsplass",
    "Fellesutgifter",
    "Reparasjon og vedlikehold av anlegg, også serviceavtaler",
    "Leie av lager/naust/garsjer og lignende",
    "Fast bygningsinventar og påkostning, leide bygg",
    "Risikoavsetning - Hærverk, enetiltak/skjerming, etc.",
    "Ombygging/flytting lokaler"
]

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def parse_line(line: str) -> Optional[Dict[str, Any]]:
    line = line.strip()
    if not line: return None

    # Match Cost Center ID (6 digits)
    match = re.search(r'Region\s+[\wØæåøÆÅ-]+\s+(\d{5,6})\s+', line)
    if not match:
        return None
    center_id = match.group(1)
    
    # Check for a property ID (5 digits for Region Sør, often 31xxx)
    # Looking for a 5 digit number that is NOT the start of the center_id and followed by a space
    prop_id_match = re.search(r'\s(31\d{3})\s', line)
    property_id = prop_id_match.group(1) if prop_id_match else None

    # Locate bureau to split
    bureau_found = None
    sorted_bureaus = sorted(BUREAUS, key=len, reverse=True)
    for b in sorted_bureaus:
        if f" {b}" in line:
            bureau_found = b
            break
            
    if not bureau_found:
        for b in sorted_bureaus:
            if b in line:
                bureau_found = b
                break
        
    if not bureau_found:
        return None
        
    # Amount is at the end
    amount_match = re.search(r'(-?[\d\s,.]+)$', line)
    if not amount_match:
        return None
        
    amount_str = amount_match.group(1).strip()
    amount_clean = amount_str.replace(',', '.')
    amount_clean = re.sub(r'[^\d.-]', '', amount_clean)
    
    try:
        amount = float(amount_clean)
    except:
        amount = 0.0
        
    # Category search
    category_found = "Annet"
    rest_for_cat = line[:amount_match.start()].strip()
    
    provider = "Ukjent"
    for cat in sorted(EXPENSE_CATEGORIES, key=len, reverse=True):
        if cat in rest_for_cat:
            category_found = cat
            cat_pos = rest_for_cat.find(cat)
            provider = rest_for_cat[cat_pos + len(cat):].strip()
            if not provider:
                # Try before if empty
                prefix = rest_for_cat[:cat_pos].strip()
                if prefix:
                    provider = prefix.split()[-1]
            break

    # Property description
    # If we have property_id, include it in key
    id_pos = line.find(center_id)
    id_end = id_pos + len(center_id)
    bureau_pos = line.find(bureau_found, id_end)
    
    property_key = line[id_end:bureau_pos].strip()
    if property_id:
        property_key = f"{property_id} {property_key}"

    return {
        "property_key": property_key,
        "category": category_found,
        "provider": provider,
        "amount": amount,
        "property_id": property_id
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

    by_property = {}
    for item in parsed_items:
        prop_key = item['property_key']
        if prop_key not in by_property:
            by_property[prop_key] = []
        by_property[prop_key].append(item)
        
    async with SessionLocal() as db:
        result = await db.execute(select(Property))
        all_properties = result.scalars().all()
        
        updated_count = 0

        for raw_key, transactions in by_property.items():
            clean_key = raw_key.lower().strip()
            # Extract 5-digit ID if present
            pid_match = re.search(r'(\d{5})', clean_key)
            pid = pid_match.group(1) if pid_match else None
            
            best_prop = None
            best_score = 0.0
            
            for p in all_properties:
                score = 0.0
                # Direct ID mismatch check for Region Sør patterns
                if pid:
                    # check if current property has this ID in external_data or if name matches
                    p_ext = p.external_data or {}
                    if pid == str(p_ext.get('internal_property_id', '')):
                        score = 1.0
                    elif pid in p.name:
                        score = 0.95
                
                if score < 0.9:
                    # Clean the key from IDs for text matching
                    match_key = re.sub(r'^\d+\s+', '', clean_key)
                    score = similar(match_key, p.name.lower())
                    addr_score = similar(match_key, (p.address or "").lower())
                    
                    if match_key in p.name.lower() or (p.address and match_key in p.address.lower()):
                        score = max(score, 0.85)
                    
                    score = max(score, addr_score)

                if score > best_score:
                    best_score = score
                    best_prop = p

            if best_score > 0.65:
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
                        "source": "docs/08.txt"
                    })
                    total_new += t['amount']
                
                fin['manual_expenses'] = existing_expenses + new_expenses
                fin['total_manual_expenses'] = fin.get('total_manual_expenses', 0.0) + total_new
                
                best_prop.external_data['financials'] = fin
                
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(best_prop, "external_data")
                db.add(best_prop)
                updated_count += 1
                
        await db.commit()
        print(f"Import Summary for 08.txt:")
        print(f"- Unique Property keys identified: {len(by_property)}")
        print(f"- Properties matched and updated: {updated_count}")
        print(f"- Total transactions imported: {len(parsed_items)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_enrichment_08.py <file_path>")
    else:
        file_path = sys.argv[1]
        asyncio.run(update_database(file_path))
