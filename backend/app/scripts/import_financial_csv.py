import sys
import os
import asyncio
import pandas as pd
import re
from difflib import SequenceMatcher
from sqlalchemy import select
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User

CSV_PATH = "backend/docs/ok1.csv"

def normalize_addr(addr):
    if not isinstance(addr, str): return ""
    # 1. Lowercase, remove special chars
    s = addr.lower().replace(",", " ").replace(".", " ").replace("-", " ")
    
    # 2. Split digits from chars (e.g. "Storgata10" -> "storgata 10")
    s = re.sub(r'(\d+)', r' \1 ', s)
    
    # 3. Standardization
    s = s.replace("veien", "vei").replace("vegen", "vei").replace("gata", "gate")
    
    # 4. Remove extra whitespace
    return " ".join(s.split())

def fuzzy_match(name1, name2):
    return SequenceMatcher(None, name1, name2).ratio()

async def import_csv_financials():
    print(f"Reading {CSV_PATH}...")
    try:
        df = pd.read_csv(CSV_PATH, sep=';', on_bad_lines='skip', engine='python')
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Normalize columns
    df.columns = [c.strip() for c in df.columns]
    
    # Required columns
    col_addr = 'Dim 2(T)'
    col_amount = 'Kontantbeløp'
    col_provider = 'Resk.nr(T)'
    col_type = 'Konto(T)'
    col_date = 'Kont.periode' # e.g. 202401
    
    if col_addr not in df.columns or col_amount not in df.columns:
        print(f"Missing required columns. Found: {df.columns}")
        return

    # 1. Group Data by Address
    print("Grouping data by address...")
    grouped_data = {}
    
    count_rows = 0
    for idx, row in df.iterrows():
        raw_addr = row.get(col_addr)
        if pd.isna(raw_addr) or str(raw_addr).strip() == "":
            continue
            
        addr_key = str(raw_addr).strip()
        
        # Parse Amount
        raw_amt = row.get(col_amount)
        amount = 0.0
        try:
            if pd.notna(raw_amt):
                s = str(raw_amt).replace('.', '').replace(',', '.')
                amount = float(s)
        except:
            amount = 0.0
            
        # Create Expense Item
        item = {
            "source": "csv",
            "date": str(row.get(col_date, "")),
            "amount_parsed": amount,
            "provider": str(row.get(col_provider, "Ukjent")),
            "type": str(row.get(col_type, "Annet")),
            "description": f"{row.get('Tekst', '')}" 
        }
        
        if addr_key not in grouped_data:
            grouped_data[addr_key] = []
        grouped_data[addr_key].append(item)
        count_rows += 1
        
    print(f"Processed {count_rows} rows across {len(grouped_data)} unique addresses.")

    # 2. Fetch Properties from DB
    async with SessionLocal() as db:
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        print(f"Loaded {len(properties)} properties from DB.")
        
        matched_count = 0
        updated_props = 0
        matched_csv_keys = set()
        
        # 3. Match and Update
        for p in properties:
            # Prepare Property Norms
            p_name_norm = normalize_addr(p.name or "")
            p_addr_norm = normalize_addr(p.address or "")
            
            best_match_key = None
            best_score = 0.0
            
            # Find best matching address from CSV keys
            # Optimization: Try exact normalized match first
            
            # Exact match check
            # We don't want to iterate 600 CSV keys for every property if we can help it.
            # But keys are "Address, Zip City". DB Address might be different.
            
            # Let's iterate keys once.
            for key in grouped_data.keys():
                k_norm = normalize_addr(key)
                
                # Check 1: Exact Address
                if k_norm == p_addr_norm:
                    best_match_key = key
                    best_score = 1.0
                    break
                
                # Check 2: Substring Match (High Confidence)
                # If DB address is inside CSV key (e.g. "Road 1" in "Road 1, City")
                if p_addr_norm and len(p_addr_norm) > 5 and p_addr_norm in k_norm:
                     best_score = 0.95
                     best_match_key = key
                     break
                # Or vice versa (less likely but possible)
                if k_norm and len(k_norm) > 5 and k_norm in p_addr_norm:
                     best_score = 0.95
                     best_match_key = key
                     break

                # Check 3: Fuzzy Address
                if p_addr_norm:
                    score = fuzzy_match(p_addr_norm, k_norm)
                    if score > best_score:
                        best_score = score
                        best_match_key = key
                
                # Check 4: Fuzzy Name (if address fails)
                if p_name_norm:
                    score = fuzzy_match(p_name_norm, k_norm)
                    if score > best_score:
                        best_score = score
                        best_match_key = key
            
            if best_score > 0.60:
                # MATCH FOUND
                matched_csv_keys.add(best_match_key)
                csv_expenses = grouped_data[best_match_key]
                
                # Update Property
                ext = dict(p.external_data or {})
                if 'financials' not in ext:
                    ext['financials'] = {}
                
                # Existing Manual Expenses (preserve them?)
                # User complaint was missing region. 
                # Let's MERGE.
                current_manual = ext['financials'].get('manual_expenses', [])
                
                # Filter out old "csv" inputs to avoid duplicates if re-run
                filtered_manual = [x for x in current_manual if x.get('source') != 'csv']
                
                # Add new CSV items
                new_manual = filtered_manual + csv_expenses
                
                # Recalculate Totals
                total_man = sum(x.get('amount_parsed', 0) for x in new_manual)
                
                ext['financials']['manual_expenses'] = new_manual
                ext['financials']['total_manual_expenses'] = total_man
                ext['financials']['total_spend_csv'] = 0 # Data moved to manual_expenses
                # Also verify total_spend_csv matches simple csv sum (optional, but good for consistency)
                # ext['financials']['total_spend_csv'] = sum(x['amount_parsed'] for x in csv_expenses)
                
                p.external_data = ext
                db.add(p)
                updated_props += 1
                matched_count += 1
                print(f"MATCH: {p.name} <-> {best_match_key} (Score: {best_score:.2f}) - Added {len(csv_expenses)} rows.")
        
        await db.commit()
        print(f"Update complete. Matched {matched_count} properties. Saved to DB.")
        
        # Report Unmatched CSV Data
        all_keys = set(grouped_data.keys())
        unmatched_keys = all_keys - matched_csv_keys
        print(f"\n--- UNMATCHED CSV ADDRESSES ({len(unmatched_keys)}) ---")
        for k in sorted(list(unmatched_keys)):
            print(f"UNMATCHED: {k}")

if __name__ == "__main__":
    asyncio.run(import_csv_financials())
