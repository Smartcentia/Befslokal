
import asyncio
import os
import sys
import csv
import random
import difflib
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# Load env vars
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.base import Property  # Ensure models are registered
from app.db.session import SessionLocal
from sqlalchemy import select
from sqlalchemy.orm import Session

# Paths
DOCS_DIR = os.path.join(os.path.dirname(__file__), '../../docs')
MASTER_FILE = os.path.join(DOCS_DIR, 'totalny.txt')

# Expense Categories & Keywords (The "Anchors" for parsing)
# Mapping: Keyword -> Category
EXPENSE_KEYWORDS = {
    "Strøm og oppvarming": "energy",
    "Renhold lokaler": "cleaning",
    "Leie lokaler": "rent", 
    "Fellesutgifter": "common_cost",
    "Vaktmestertjenester": "janitor",
    "Renovasjon, vann, avløp": "municipal",
    "Reparasjon og vedlikehold": "maintenance",
    "Oppgradering og påkostning": "maintenance_upgrade",
    "Annen kostnad lokaler": "other",
    "Vakthold lokaler": "security",
    "Energi til leieobjektet": "energy"
}

# Standardized Costs for Synthesis (Fallback)
SYNTHETIC_DEFAULTS = {
    "energy": {"base": 150, "var": 0.3},
    "cleaning": {"base": 120, "var": 0.2},
    "maintenance": {"base": 80, "var": 0.5},
    "janitor": {"base": 50, "var": 0.1},
    "municipal": {"base": 40, "var": 0.1},
}

def parse_float(value):
    if not value: return 0.0
    try:
        # Handle Norwegian format: "1.234,56" or "1 234,56" -> 1234.56
        # But text files seem to use "," as decimal and no thousand sep, or space?
        # In 02.txt: "113721,2" -> 113721.2
        val = value.replace(',', '.')
        # Remove spaces that act as thousand separators? "21 973" -> "21973"
        # But be careful not to remove spaces if it's not a number. 
        # Here we assume 'value' is the extracted amount string.
        val = val.replace(' ', '').replace('\xa0', '')
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def fuzzy_match(title: str, choices: List[str], cutoff=0.6) -> str:
    # Normalize
    title = title.lower().replace('familievernkontoret', 'fvk').replace('ungdomssenter', 'us')
    choices_map = {c.lower().replace('familievernkontoret', 'fvk').replace('ungdomssenter', 'us'): c for c in choices}
    
    matches = difflib.get_close_matches(title, choices_map.keys(), n=1, cutoff=cutoff)
    if matches:
        return choices_map[matches[0]]
    return None

async def import_master_data() -> Dict[str, Dict]:
    """Parses totalny.txt to get the Source of Truth for properties."""
    print(f"📦 Parsing Master Data: {MASTER_FILE}")
    master_db = {} 
    
    if not os.path.exists(MASTER_FILE):
        print("❌ Master file not found!")
        return {}

    with open(MASTER_FILE, 'r', encoding='utf-8', errors='replace') as f:
        # Check first line to determine delimiter
        first_line = f.readline()
        f.seek(0)
        delimiter = '\t' if '\t' in first_line else ',' # Fallback
        
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            # Name candidates
            name = row.get('Avtalenavn')
            if not name or len(name) < 3:
                name = row.get('Adresselinje 1')
            
            if name:
                # Clean up area
                area_str = row.get('Areal inkl fellesareal i leiekontrakt (kvm)', '0')
                if not area_str or not area_str[0].isdigit():
                    area_str = row.get('Areal', '0')
                
                row['_parsed_area'] = parse_float(area_str)
                master_db[name] = row
                
    print(f"   ✅ Loaded {len(master_db)} properties from master.")
    return master_db

def parse_ledger_line(line: str) -> Dict:
    """
    Smart Parser for 'Region Account Property Expense Supplier Amount' lines.
    Strategy: Find Expense Keyword -> Split. 
    """
    line = line.strip()
    if not line: return None
    
    # 1. Find Expense Keyword
    found_keyword = None
    keyword_index = -1
    
    for kw in EXPENSE_KEYWORDS:
        # We assume spaces around keyword to avoid partial matches inside words, 
        # but exact match search in line is usually safe enough for these specific phrases.
        idx = line.find(kw)
        if idx != -1:
            # We want the *first* occurrence? Or matches?
            # Usually these phrases are unique in the line.
            found_keyword = kw
            keyword_index = idx
            break
            
    if not found_keyword:
        return None # Skip line if unrecognized expense (filters out header/noise)

    # 2. Split Line
    # Left part: Region ... Account ... Property Name
    # Right part: Supplier ... Amount
    left_part = line[:keyword_index].strip()
    right_part = line[keyword_index + len(found_keyword):].strip()
    
    # 3. Extract Amount from Right Part (Last token)
    # Be careful with suppliers having numbers? Usually amount is at the very end.
    right_tokens = right_part.split()
    if not right_tokens:
        return None
        
    amount_str = right_tokens[-1]
    supplier = " ".join(right_tokens[:-1])
    
    # Validate Amount
    # If amount_str is not a number (e.g. Supplier name continues), then maybe format is different?
    # In 02.txt: ... ISS Facility Services AS 1250 -> OK
    # In file: ... AS -92,69 -> OK
    try:
        amount = parse_float(amount_str)
    except:
        # Failed to parse amount, ignore line
        return None

    # 4. Extract Property Name from Left Part
    # Look for 6-digit Account Code as Anchor
    # Pattern: [Region Info] [6-digits] [Property Name] [Function?]
    # Regex for 6 digits: \b\d{6}\b
    match = re.search(r'\b\d{6}\b', left_part)
    if match:
        # Property name is EVERYTHING after the account code
        # But before the Expense Keyword (which we already stripped)
        raw_prop_name = left_part[match.end():].strip()
        
        # Cleanup: Remove likely function words
        noise_words = [
            "Familieverntjeneste", "Barnevernsinstitusjoner", 
            "Omsorg for ungdom", "Fosterhjem", "Senter for foreldre og barn",
            "Spisskompetansemiljø", "Region Nord", "Region Midt", "Region Vest", "Region Sør", "Region Øst"
        ]
        
        prop_name = raw_prop_name
        for noise in noise_words:
            prop_name = prop_name.replace(noise, "").strip()
            
        # Also clean up double spaces
        prop_name = " ".join(prop_name.split())
    else:
        # No account code? Maybe tab separated file?
        # If tab separated, the logic above (find keyword string) might still work 
        # identifying the column, but let's stick to this heuristic logic for now.
        return None

    return {
        "property_match_string": prop_name,
        "type": EXPENSE_KEYWORDS[found_keyword],
        "original_type": found_keyword,
        "supplier": supplier,
        "amount": amount,
        "date": "2024-01-01" # Placeholder, files don't seem to have dates on every line?
    }

async def process_ledgers(master_keys: List[str]) -> Tuple[Dict[str, List[Dict]], Dict[str, set]]:
    """Iterates 01.txt...17.txt and extracts data linked to master properties."""
    print("🕵️  Processing Ledgers (01.txt - 17.txt)...")
    
    property_expenses = {} # MasterName -> List[Expenses]
    global_suppliers = {cat: set() for cat in SYNTHETIC_DEFAULTS.keys()}
    global_suppliers['rent'] = set()
    global_suppliers['other'] = set() # Add extras
    global_suppliers['common_cost'] = set()
    global_suppliers['maintenance_upgrade'] = set()
    global_suppliers['security'] = set()

    
    files = sorted([f for f in os.listdir(DOCS_DIR) if f.endswith('.txt') and (f[:2].isdigit() or f == 'totalny.txt')])
    # Filter for ledger files (exclude total/totalny/readme etc if any)
    ledger_files = [f for f in files if f[:2].isdigit()]
    
    print(f"   Found {len(ledger_files)} ledger files: {ledger_files}")
    
    stats_lines = 0
    stats_matches = 0
    
    for fname in ledger_files:
        path = os.path.join(DOCS_DIR, fname)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                stats_lines += 1
                record = parse_ledger_line(line)
                if not record: continue
                
                # Capture Supplier for synthesis pool
                cat = record['type']
                if cat in global_suppliers:
                    global_suppliers[cat].add(record['supplier'])
                
                # Match to Property
                # We fuzzy match the extracted 'property_match_string' against Master Keys
                match = fuzzy_match(record['property_match_string'], master_keys)
                if match:
                    if match not in property_expenses:
                        property_expenses[match] = []
                    property_expenses[match].append(record)
                    stats_matches += 1
    
    print(f"   Processed {stats_lines} lines. Matched {stats_matches} transactions to properties.")
    return property_expenses, global_suppliers

from sqlalchemy.orm.attributes import flag_modified

async def main():
    print("🚀 Starting Advanced Data Import...")
    
    async with SessionLocal() as session:
        # 1. Master Data
        master_data = await import_master_data()
        master_keys = list(master_data.keys())
        
        if not master_keys:
            print("⚠️ No master data found. Aborting.")
            return

        # 2. Ledger Data
        real_expenses, suppliers = await process_ledgers(master_keys)
        
        # 3. Update Database
        print("💾 Updating Database...")
        db_props = await session.execute(select(Property))
        db_props = db_props.scalars().all()
        
        updates = 0
        matches_with_data = 0
        
        print(f"   🔍 Debug: Real Expenses Keys (Sample): {list(real_expenses.keys())[:5]}")
        
        for prop in db_props:
            # Find Master Match
            m_key = fuzzy_match(prop.name, master_keys)
            
            # Debug Matching
            if updates < 5:
                print(f"      Prop: '{prop.name}' -> Match: '{m_key}'")
            
            m_data = master_data.get(m_key) if m_key else None
            
            # COPY dictionary to ensure SQLAlchemy detects change on reassignment
            ext_data = dict(prop.external_data) if prop.external_data else {}
            
            # A. Update Master Info
            real_area = 0
            if m_data:
                ext_data['master_data'] = m_data
                real_area = m_data.get('_parsed_area', 0)
                ext_data['area'] = real_area
                ext_data['landlord'] = m_data.get('Utleier')
            
            # B. Insert Expenses (Real or Synthetic fallback)
            prop_expenses = real_expenses.get(m_key, [])
            
            final_expenses = []
            
            if prop_expenses:
                # USE REAL DATA
                final_expenses = prop_expenses
                ext_data['data_source'] = 'real_ledger'
                matches_with_data += 1
                if matches_with_data <= 5:
                     print(f"      ✅ MATCH WITH DATA: {prop.name} -> {m_key} ({len(prop_expenses)} items)")
            else:
                # GENERATE SYNTHETIC (Fallback)
                ext_data['data_source'] = 'synthetic'
                # Use area fallback
                sim_area = real_area if real_area > 0 else 500
                
                for cat, cfg in SYNTHETIC_DEFAULTS.items():
                    # Pick supplier from real pool if possible
                    pool = list(suppliers.get(cat, []))
                    supp = random.choice(pool) if pool else "Ukjent Leverandør"
                    
                    cost = sim_area * cfg['base'] * random.uniform(1 - cfg['var'], 1 + cfg['var'])
                    final_expenses.append({
                        "type": cat,
                        "supplier": supp,
                        "amount": round(cost, 2),
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "is_synthetic": True
                    })
            
            # Check structure
            if 'financials' not in ext_data: ext_data['financials'] = {}
            ext_data['financials']['manual_expenses'] = final_expenses
            
            # Calc Cost Summary for search
            total_cost = sum(e['amount'] for e in final_expenses if e['type'] != 'rent') # Exclude rent from "costs" usually?
            rent_cost = sum(e['amount'] for e in final_expenses if e['type'] == 'rent')
            
            ext_data['financials']['cost_summary'] = total_cost
            ext_data['financials']['rent_summary'] = rent_cost
            
            prop.external_data = ext_data
            flag_modified(prop, "external_data") # Force update
            
            session.add(prop)
            updates += 1
            
        await session.commit()
        print(f"✅ Updated {updates} properties. (Real Data Used: {len(real_expenses)} props)")

if __name__ == "__main__":
    asyncio.run(main())
