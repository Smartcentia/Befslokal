
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

# Load env
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal

# Import related models FIRST to avoid Circular/InvalidRequestError
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.user import User
from app.domains.core.models.party import Party
# Import Property LAST
from app.domains.core.models.property import Property
from sqlalchemy.orm.attributes import flag_modified

# --- Configuration ---
DOCS_DIR = "docs"
FILES_TO_PROCESS = [f"{i:02d}.txt" for i in range(1, 18)]

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
    "Administrasjon",
    "Enhet for inntak",
    "Prosjektering og utvikling av eiendom/bygg",
    "Større anskaffelser",
    "Selvassuranse",
    "Tverrfaglig helsekartlegging av barn i barnevernet",
    "Enhet for spesialiserte fosterhjem - region Øst",
    "Seksjon adopsjon"
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

def clean_amount(amount_str: str) -> float:
    # Basic cleaning: replace comma with dot, remove non-numeric chars (except dot and minus)
    # Handle "1.000,00" -> "1000.00"
    # Or "1 000,00" -> "1000.00"
    
    # Remove spaces
    s = amount_str.replace(" ", "")
    # Replace comma with dot
    s = s.replace(",", ".")
    # Remove anything that is not digit, dot, or minus
    s = re.sub(r'[^\d.-]', '', s)
    
    # Handle multiple dots? e.g. 1.000.00
    if s.count('.') > 1:
        # Assume last dot is decimal, others are thousands separators
        parts = s.split('.')
        s = "".join(parts[:-1]) + "." + parts[-1]
        
    try:
        return float(s)
    except:
        return 0.0

def parse_line(line: str) -> Optional[Dict[str, Any]]:
    line = line.strip()
    if not line: return None
    
    # Match Cost Center ID (5 or 6 digits) - usually early in line
    match = re.search(r'Region\s+[\wØæåøÆÅ-]+\s+(\d{5,6})\s+', line)
    
    # Fallback: Some lines might not have "Region X" prefix perfectly matched if we just look for digits
    # But let's stick to the pattern we used before which mostly worked, except the amount greediness.
    
    center_id = None
    if match:
        center_id = match.group(1)
    else:
        # Try to find just the first 5-6 digit block?
        # Let's keep strictness to avoid garbage lines
        return None
    
    # Check for a property ID (7 digits)
    prop_id_match = re.search(r'\b(\d{7})\b', line)
    property_id = None
    if prop_id_match:
        if prop_id_match.group(1) != center_id:
            property_id = prop_id_match.group(1)

    # Locate bureau 
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
        
    # --- IMPROVED PARSING STRATEGY: CATEGORY FIRST ---
    # We match known categories first to avoid trapping numbers inside category names (e.g. "kr 50 000")
    # into the amount regex.
    
    category_found = "Annet"
    provider = "Ukjent"
    amount = 0.0
    
    # We search for the category in the part of the line AFTER the bureau (heuristic)
    # But simply searching the whole line is safer given fixed strings.
    
    match_cat = None
    cat_end_pos = 0
    
    sorted_cats = sorted(EXPENSE_CATEGORIES, key=len, reverse=True)
    for cat in sorted_cats:
        idx = line.find(cat)
        if idx != -1:
            match_cat = cat
            cat_end_pos = idx + len(cat)
            category_found = cat
            break
            
    # Determine the text segment to search for amount
    if match_cat:
        # Amount is in the substring AFTER the category
        search_segment = line[cat_end_pos:]
        
        # Provider is also in this segment, usually before the amount.
        # But we need to extract amount from the END of this segment.
        amount_match = re.search(r'(-?[\d\s,.]+)$', search_segment)
    else:
        # No category found, search from end of line
        search_segment = line
        amount_match = re.search(r'(-?[\d\s,.]+)$', line)

    if amount_match:
        captured_str = amount_match.group(1).strip()
        # Remove leading punctuation (e.g. captured comma from "AS, 123")
        captured_str = captured_str.lstrip(",. ")
        
        # --- Apply the Split Token Logic (for Account Codes and IDs) ---
        tokens = captured_str.split()
        
        # 1. Check for PRECEDING large integer (ID/KID/Account)
        # If the first token is a 4+ digit integer, it cannot be a thousands-group.
        if len(tokens) > 1:
            # Clean token 0 of punctuation for check
            t0_clean = tokens[0].strip(",.")
            if re.match(r'^\d{4,}$', t0_clean):
                # First token is 4+ digits integer. It's an ID. Drop it.
                tokens.pop(0)

        valid_amount = 0.0
        
        if len(tokens) > 1:
            last_token = tokens[-1]
            # Clean last token for check
            last_clean = last_token.strip(",.")
            
            if re.match(r'^\d{4,8}$', last_clean):
                # Is account code
                potential_amount_str = " ".join(tokens[:-1])
                valid_amount = clean_amount(potential_amount_str)
            else:
                 valid_amount = clean_amount(" ".join(tokens))
        else:
             if tokens:
                valid_amount = clean_amount(tokens[0])
             else:
                valid_amount = 0.0
        
        amount = valid_amount
        
        # Now extract Provider
        # Provider is the text in search_segment BEFORE the amount match
        # search_segment = " ProviderName 123,00"
        
        amt_start_in_seg = amount_match.start()
        provider_part = search_segment[:amt_start_in_seg].strip()
        if provider_part:
            provider = provider_part
    else:
        return None

    # Property key extraction
    property_key = ""
    start_pos = 0
    if property_id:
        pid_pos = line.find(property_id)
        start_pos = pid_pos + len(property_id)
    else:
        id_pos = line.find(center_id)
        start_pos = id_pos + len(center_id)
        
    bureau_pos = line.find(bureau_found, start_pos)
    
    if bureau_pos > start_pos:
        property_key = line[start_pos:bureau_pos].strip()

    if property_id:
        property_key = f"{property_id} {property_key}".strip()

    return {
        "property_key": property_key,
        "category": category_found,
        "provider": provider,
        "amount": amount,
        "property_id": property_id
    }

    # Property key extraction
    property_key = ""
    start_pos = 0
    if property_id:
        pid_pos = line.find(property_id)
        start_pos = pid_pos + len(property_id)
    else:
        id_pos = line.find(center_id)
        start_pos = id_pos + len(center_id)
        
    bureau_pos = line.find(bureau_found, start_pos)
    
    if bureau_pos > start_pos:
        property_key = line[start_pos:bureau_pos].strip()

    if property_id:
        property_key = f"{property_id} {property_key}".strip()

    return {
        "property_key": property_key,
        "category": category_found,
        "provider": provider,
        "amount": amount,
        "property_id": property_id
    }

async def clear_existing_financials():
    print("Clearing existing financials from all properties...")
    async with SessionLocal() as db:
        result = await db.execute(select(Property))
        all_props = result.scalars().all()
        
        count = 0
        for p in all_props:
            if p.external_data and 'financials' in p.external_data:
                # We want to clear manual_expenses but maybe keep other things if they existed?
                # Actually, the task is to re-import ALL manual_expenses. 
                # Assuming all manual_expenses came from these files.
                
                fin = p.external_data['financials']
                if 'manual_expenses' in fin:
                    fin['manual_expenses'] = []
                    fin['total_manual_expenses'] = 0.0
                    
                    # Force update
                    p.external_data['financials'] = fin
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(p, "external_data")
                    db.add(p)
                    count += 1
        
        await db.commit()
        print(f"Cleared financials for {count} properties.")

async def process_file(filename: str, seen_internal_global: set, exclusion_set: set):
    file_path = os.path.join(DOCS_DIR, filename)
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"\nProcessing {filename}...")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    unique_lines = []
    
    skipped_internal = 0
    skipped_cross = 0
    
    # Local internal dedupe for this file? 
    # Or should we dedupe globally? The requirement was:
    # 1. Internal dedupe (within file)
    # 2. Cross-file dedupe (against previous files)
    
    # We can maintain a global 'seen' set across all files to handle everything locally and cross-file efficiently.
    # But strictly following previous logic:
    # docs/15.txt checked against 11 and 08. 
    # But if we run them in order 01..17, we can just accumulate ALL seen lines.
    
    updated_local_seen = set()
    
    for line in lines:
        stripped = line.strip()
        if not stripped: continue
        
        if stripped in updated_local_seen:
            skipped_internal += 1
            continue
        updated_local_seen.add(stripped)
        
        if stripped in exclusion_set:
            skipped_cross += 1
            continue
            
        unique_lines.append(stripped)
        # Add to exclusion set for FUTURE files
        exclusion_set.add(stripped)
        
    print(f"Lines: {len(lines)} | Valid: {len(unique_lines)} | Skipped Int: {skipped_internal} | Skipped Cross: {skipped_cross}")
    
    parsed_items = []
    for line in unique_lines:
        p = parse_line(line)
        if p:
            parsed_items.append(p)
            
    # Group by property
    by_property = {}
    for item in parsed_items:
        prop_key = item['property_key']
        if not prop_key: continue
        if prop_key not in by_property:
            by_property[prop_key] = []
        by_property[prop_key].append(item)
        
    # DB Update
    async with SessionLocal() as db:
        result = await db.execute(select(Property))
        all_properties = result.scalars().all()
        
        updated_count = 0
        
        for raw_key, transactions in by_property.items():
            clean_key = raw_key.lower().strip()
            
            # Match Logic
            pid_match = re.search(r'(\d{7})', clean_key)
            pid = pid_match.group(1) if pid_match else None
            
            best_prop = None
            best_score = 0.0
            
            for p in all_properties:
                # Skip properties without names
                if not p.name:
                    continue
                    
                score = 0.0
                if pid:
                    if pid in p.name or (p.address and pid in p.address):
                        score = 1.0
                if score < 1.0:
                    match_key_text = re.sub(r'^\d+\s+', '', clean_key)
                    if not match_key_text: continue
                    score_name = similar(match_key_text, p.name.lower())
                    score_addr = similar(match_key_text, (p.address or "").lower())
                    score = max(score_name, score_addr)
                    
                    if match_key_text in p.name.lower(): score = max(score, 0.85)
                    if p.address and match_key_text in p.address.lower(): score = max(score, 0.85)
            
                if score > best_score:
                    best_score = score
                    best_prop = p
                    
            if best_score > 0.65:
                if not best_prop.external_data:
                    best_prop.external_data = {}
                
                fin = best_prop.external_data.get('financials', {})
                if not isinstance(fin, dict): fin = {}
                
                existing = fin.get('manual_expenses', [])
                
                new_expenses = []
                total_new = 0.0
                
                for t in transactions:
                    new_expenses.append({
                        "type": t['category'],
                        "provider": t['provider'],
                        "amount": t['amount'],
                        "amount_parsed": t['amount'],
                        "date": "2026-Q1",
                        "source": f"docs/{filename}"
                    })
                    total_new += t['amount']
                    
                fin['manual_expenses'] = existing + new_expenses
                fin['total_manual_expenses'] = fin.get('total_manual_expenses', 0.0) + total_new
                
                best_prop.external_data['financials'] = fin
                flag_modified(best_prop, "external_data")
                db.add(best_prop)
                updated_count += 1
                
        await db.commit()
    return updated_count

async def main():
    print("Starting Global Re-import Process...")
    
    # 1. Clear DB
    await clear_existing_financials()
    
    # 2. Process Files sequentially
    # We maintain a growing 'exclusion_set' which effectively handles cross-file deduplication
    # as we go from 01 to 17.
    
    global_exclusion_set = set()
    
    for filename in FILES_TO_PROCESS:
        await process_file(filename, set(), global_exclusion_set)
        
    print("\nGlobal Re-import Complete.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-parse":
        # Test mode to verify regex
        test_lines = [
            "5 Region Midt-Norge 520601 Skatval ungdomssenter 53910 Ekstra innkjøp Barnevernsinstitusjoner Leie lokaler -544047",
            "3 Region Sør 334001 Agder 50000 Barnevernsinstitusjoner Leie lokaler 1200,50 50000", 
            "3 Region Sør 334001 Agder 50000 Barnevernsinstitusjoner Leie lokaler 1 200,50", 
            "3 Region Sør 334001 Agder 50000 Barnevernsinstitusjoner Leie lokaler 50000",
            "5 Region Midt-Norge 522801 Buvika ungdomssenter Barnevernsinstitusjoner Fast bygningsinventar over kr 50 000 146032,4",
            "3 Region Sør 321402 St.Hansgården Barnevernsinstitusjoner Annen kostnad lokaler R. Dovland AS, 15033440445 1403,55"
        ]
        for l in test_lines:
            print(f"Line: {l}")
            print(f"Parsed: {parse_line(l)}\n")
    else:
        asyncio.run(main())
