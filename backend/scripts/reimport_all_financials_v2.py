
import asyncio
import sys
import os
import re
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from difflib import SequenceMatcher
from dotenv import load_dotenv

# Add backend to path if not already there
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

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
# Import Center to avoid relationship error
from app.domains.core.models.center import Center
# Import Property LAST
from app.domains.core.models.property import Property
from sqlalchemy.orm.attributes import flag_modified

# --- Configuration ---
DOCS_DIR = "docs"
FILES_TO_PROCESS = [f"{i:02d}.txt" for i in range(1, 18)]

# Lowered from 0.65 to 0.50
MATCH_THRESHOLD = 0.50

# Region mapping from txt files to standardformat (se docs/REGION_STANDARD.md)
REGION_MAP = {
    "region nord": "Nord",
    "region midt-norge": "Midt-Norge",
    "region midt": "Midt-Norge",
    "region vest": "Vest",
    "region sør": "Sør",
    "region øst": "Øst",
    "bufdir": "Bufdir",
}

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

# Common suffixes to normalize for matching
NAME_SUFFIXES = [
    "ungdomssenter", "ungdomsheim", "ungdomshjem", "ungdomsbase",
    "omsorgssenter", "familiesenter", "barnesenter",
    "avdeling", "avd.", "avd",
]

# Special property key patterns that map to regional offices
REGIONAL_OFFICE_PATTERNS = {
    "regionkontor felleskostnader": "regionkontor",
    "felleskostnader": "regionkontor",
    "driftsavdelingen": "bufetat",
    "region midt-norge felleskostnader": "bufetat trondheim",
    "region vest felleskostnader": "bufetat",
    "region sør felleskostnader": "bufetathus",
    "region øst felleskostnader": "regionkontoret",
    "region nord felleskostnader": "regionkontor",
}

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def normalize_name(name: str) -> str:
    """Normalize property name for better matching."""
    name = name.lower().strip()
    # Remove common suffixes
    for suffix in NAME_SUFFIXES:
        name = name.replace(suffix, "").strip()
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name)
    return name

def extract_tokens(text: str) -> set:
    """Extract significant tokens from text."""
    text = text.lower()
    # Remove numbers at start
    text = re.sub(r'^\d+\s+', '', text)
    # Split and filter short tokens
    tokens = set(t for t in re.split(r'\W+', text) if len(t) > 2)
    return tokens

def token_overlap_score(a: str, b: str) -> float:
    """Calculate token overlap ratio."""
    tokens_a = extract_tokens(a)
    tokens_b = extract_tokens(b)
    if not tokens_a or not tokens_b:
        return 0.0
    overlap = tokens_a & tokens_b
    return len(overlap) / min(len(tokens_a), len(tokens_b))

def clean_amount(amount_str: str) -> float:
    s = amount_str.replace(" ", "")
    s = s.replace(",", ".")
    s = re.sub(r'[^\d.-]', '', s)

    if s.count('.') > 1:
        parts = s.split('.')
        s = "".join(parts[:-1]) + "." + parts[-1]

    try:
        return float(s)
    except:
        return 0.0

def parse_line(line: str) -> Optional[Dict[str, Any]]:
    line = line.strip()
    if not line: return None

    # Extract region from line
    region_match = re.search(r'Region\s+([\wØæåøÆÅ-]+)', line)
    region = None
    if region_match:
        region_text = f"region {region_match.group(1)}".lower()
        region = REGION_MAP.get(region_text)

    # Match Cost Center ID (5 or 6 digits)
    match = re.search(r'Region\s+[\wØæåøÆÅ-]+\s+(\d{5,6})\s+', line)

    center_id = None
    if match:
        center_id = match.group(1)
    else:
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

    category_found = "Annet"
    provider = "Ukjent"
    amount = 0.0

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

    if match_cat:
        search_segment = line[cat_end_pos:]
        amount_match = re.search(r'(-?[\d\s,.]+)$', search_segment)
    else:
        search_segment = line
        amount_match = re.search(r'(-?[\d\s,.]+)$', line)

    if amount_match:
        captured_str = amount_match.group(1).strip()
        captured_str = captured_str.lstrip(",. ")

        tokens = captured_str.split()

        if len(tokens) > 1:
            t0_clean = tokens[0].strip(",.")
            if re.match(r'^\d{4,}$', t0_clean):
                tokens.pop(0)

        valid_amount = 0.0

        if len(tokens) > 1:
            last_token = tokens[-1]
            last_clean = last_token.strip(",.")

            if re.match(r'^\d{4,8}$', last_clean):
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

    # IMPROVED: Check if property_key looks like just a number (likely an amount or code)
    # If so, try to extract a better key from the line
    if property_key and re.match(r'^\d+$', property_key.strip()):
        # This is just a number - probably misidentified
        # First, try to find the REAL property name by looking at the line structure
        # Pattern: "Region X NNNNNN PropertyName OptionalCode Bureau Category..."

        # Try to extract property name between center_id and bureau
        full_segment = line[line.find(center_id) + len(center_id):bureau_pos].strip()

        # Remove leading numbers (optional property codes like 151003)
        cleaned_segment = re.sub(r'^\d+\s+', '', full_segment)
        # Remove trailing numbers (amounts that got included)
        cleaned_segment = re.sub(r'\s+\d+$', '', cleaned_segment)

        if cleaned_segment and not re.match(r'^\d+$', cleaned_segment):
            # Found a non-numeric name
            property_key = cleaned_segment
        else:
            # Try to find a descriptive name before the bureau
            # Look for patterns like "Regionkontor felleskostnader" etc.
            for pattern, _ in REGIONAL_OFFICE_PATTERNS.items():
                if pattern.lower() in line.lower():
                    property_key = pattern
                    break
            else:
                # Still just a number - mark it for regional office matching
                if "felleskostnader" in line.lower() or "regionkontor" in line.lower():
                    property_key = "regionkontor felleskostnader"
                elif "driftsavdeling" in line.lower():
                    property_key = "driftsavdelingen"
                # Keep original if no pattern matches

    return {
        "property_key": property_key,
        "category": category_found,
        "provider": provider,
        "amount": amount,
        "property_id": property_id,
        "region": region  # Added region for filtering
    }

async def clear_existing_financials():
    print("Clearing existing financials from all properties...")
    async with SessionLocal() as db:
        result = await db.execute(select(Property))
        all_props = result.scalars().all()

        count = 0
        for p in all_props:
            if p.external_data and 'financials' in p.external_data:
                fin = p.external_data['financials']
                if 'manual_expenses' in fin:
                    fin['manual_expenses'] = []
                    fin['total_manual_expenses'] = 0.0

                    p.external_data['financials'] = fin
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(p, "external_data")
                    db.add(p)
                    count += 1

        await db.commit()
        print(f"Cleared financials for {count} properties.")

async def process_file(filename: str, seen_internal_global: set, exclusion_set: set, unmatched_log: list):
    file_path = os.path.join(DOCS_DIR, filename)
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return 0

    print(f"\nProcessing {filename}...")

    with open(file_path, 'r') as f:
        lines = f.readlines()

    unique_lines = []

    skipped_internal = 0
    skipped_cross = 0

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
            item_region = transactions[0].get('region')  # Use region from first transaction

            # Match Logic - ENHANCED
            pid_match = re.search(r'(\d{7})', clean_key)
            pid = pid_match.group(1) if pid_match else None

            best_prop = None
            best_score = 0.0

            # Normalized key for better matching
            normalized_key = normalize_name(clean_key)
            key_tokens = extract_tokens(clean_key)

            # Check if this is a regional office pattern
            is_regional_office = any(pattern in clean_key for pattern in REGIONAL_OFFICE_PATTERNS.keys())

            for p in all_properties:
                if not p.name:
                    continue

                score = 0.0

                # 1. Exact 7-digit ID match (highest priority)
                if pid:
                    if pid in p.name or (p.address and pid in p.address):
                        score = 1.0

                if score < 1.0:
                    match_key_text = re.sub(r'^\d+\s+', '', clean_key)
                    if not match_key_text:
                        continue

                    # 2. Region filter - boost score if same region
                    region_bonus = 0.0
                    if item_region and p.region:
                        if item_region == p.region:
                            region_bonus = 0.15  # Boost for same region

                    # 3. Normalized name matching
                    normalized_prop = normalize_name(p.name)
                    score_normalized = similar(normalized_key, normalized_prop)

                    # 4. Standard similarity
                    score_name = similar(match_key_text, p.name.lower())
                    score_addr = similar(match_key_text, (p.address or "").lower())

                    # 5. Token overlap (handles reordered words)
                    token_score = token_overlap_score(match_key_text, p.name)

                    # Combine scores
                    base_score = max(score_name, score_addr, score_normalized, token_score * 0.9)
                    score = base_score + region_bonus

                    # 6. Substring match bonus
                    if match_key_text in p.name.lower():
                        score = max(score, 0.85)
                    if p.address and match_key_text in p.address.lower():
                        score = max(score, 0.85)

                    # 7. Key words in property name (partial match)
                    prop_tokens = extract_tokens(p.name)
                    if key_tokens and prop_tokens:
                        # If main identifying word matches
                        for kt in key_tokens:
                            if len(kt) > 4:  # Only significant words
                                for pt in prop_tokens:
                                    if kt in pt or pt in kt:
                                        score = max(score, 0.70)

                    # 8. Special handling for regional offices
                    if is_regional_office:
                        p_name_lower = p.name.lower()
                        # Match "regionkontor felleskostnader" to properties containing regionkontor/bufetat
                        if "regionkontor" in clean_key or "felleskostnader" in clean_key:
                            if "regionkontor" in p_name_lower or "bufetat" in p_name_lower:
                                # Boost significantly if same region
                                if item_region and p.region and item_region == p.region:
                                    score = max(score, 0.90)
                                else:
                                    score = max(score, 0.60)
                        if "driftsavdeling" in clean_key:
                            if "bufetat" in p_name_lower or "driftsavd" in p_name_lower:
                                if item_region and p.region and item_region == p.region:
                                    score = max(score, 0.90)
                                else:
                                    score = max(score, 0.60)

                if score > best_score:
                    best_score = score
                    best_prop = p

            # LOWERED THRESHOLD from 0.65 to 0.50
            if best_score > MATCH_THRESHOLD:
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
            else:
                # Log unmatched for analysis
                unmatched_log.append({
                    "key": raw_key,
                    "region": item_region,
                    "best_score": best_score,
                    "best_match": best_prop.name if best_prop else None,
                    "transaction_count": len(transactions),
                    "total_amount": sum(t['amount'] for t in transactions)
                })

        await db.commit()
    return updated_count

async def main():
    print("Starting Enhanced Re-import Process (v2)...")
    print(f"Match threshold: {MATCH_THRESHOLD}")

    # 1. Clear DB
    await clear_existing_financials()

    # 2. Process Files sequentially
    global_exclusion_set = set()
    unmatched_log = []
    total_updated = 0

    for filename in FILES_TO_PROCESS:
        count = await process_file(filename, set(), global_exclusion_set, unmatched_log)
        total_updated += count or 0

    print(f"\n{'='*60}")
    print(f"Global Re-import Complete.")
    print(f"Total properties updated: {total_updated}")
    print(f"Unmatched property keys: {len(unmatched_log)}")

    # Write unmatched to file for analysis
    if unmatched_log:
        # Sort by total amount (most significant first)
        unmatched_log.sort(key=lambda x: -x['total_amount'])

        with open("unmatched_properties.txt", "w") as f:
            f.write(f"Unmatched Property Keys ({len(unmatched_log)} total)\n")
            f.write("="*80 + "\n\n")
            for item in unmatched_log[:50]:  # Top 50 by amount
                f.write(f"Key: {item['key']}\n")
                f.write(f"  Region: {item['region']}\n")
                f.write(f"  Best score: {item['best_score']:.2f}\n")
                f.write(f"  Best match: {item['best_match']}\n")
                f.write(f"  Transactions: {item['transaction_count']}\n")
                f.write(f"  Total amount: {item['total_amount']:,.2f}\n")
                f.write("-"*40 + "\n")

        print(f"\nUnmatched keys written to: unmatched_properties.txt")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--dry-run":
        print("Dry run mode - not implemented yet")
    else:
        asyncio.run(main())
