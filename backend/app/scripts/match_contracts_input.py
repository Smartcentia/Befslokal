
import sys
import os
import pandas as pd
import re
from difflib import SequenceMatcher

# Paths
ARTIFACT_REPORT_PATH = "/Users/frank/.gemini/antigravity/brain/65b7f27e-44cd-4c33-87af-b0192b353a08/contract_property_overview.md"
INPUT_MD_PATH = "/Users/frank/BEFS3/KNOWME/input.md"
FALLBACK_CSV_PATH = "/Users/frank/BEFS3/KNOWME/backend/data/csv_portfolio_data.csv"
OUTPUT_PATH = "/Users/frank/BEFS3/KNOWME/matched_results.md"

def normalize_addr(addr):
    if not isinstance(addr, str): return ""
    # Lowercase, remove commas, common types
    addr = addr.lower().replace(",", "").replace(".", "")
    addr = re.sub(r'\s+', ' ', addr).strip()
    return addr

def fuzzy_match(a, b, threshold=0.85):
    return SequenceMatcher(None, a, b).ratio() > threshold

def parse_markdown_table(file_path):
    data = []
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        headers = []
        for line in lines:
            if line.strip().startswith("|") and "---" not in line:
                if not headers:
                    headers = [c.strip() for c in line.strip().split('|') if c.strip()]
                else:
                    values = [c.strip() for c in line.strip().split('|') if c.strip()]
                    if len(values) == len(headers):
                        item = dict(zip(headers, values))
                        data.append(item)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        
    return pd.DataFrame(data)

def load_input_data():
    # Try input.md first
    # Assuming input.md might be csv or markdown. If it's 0 bytes, skip.
    if os.path.exists(INPUT_MD_PATH) and os.path.getsize(INPUT_MD_PATH) > 0:
        print(f"Reading {INPUT_MD_PATH}...")
        # Check if it looks like CSV or MD
        try:
            # Try sniffing first or assume ID (\t) based on file view
            return pd.read_csv(INPUT_MD_PATH, sep='\t', engine='python', on_bad_lines='skip')
        except:
            # Fallback to simple line reading or MD parsing if needed
            print(f"Could not parse {INPUT_MD_PATH} as CSV/Table. implementation pending for unstructured.")
            return pd.DataFrame()
            
    # Fallback
    if os.path.exists(FALLBACK_CSV_PATH):
        print(f"Input empty. Falling back to {FALLBACK_CSV_PATH}...")
        try:
            # Use on_bad_lines='skip' to handle inconsistent rows
            return pd.read_csv(FALLBACK_CSV_PATH, sep=';', on_bad_lines='skip', engine='python')
        except Exception as e:
            print(f"Error reading fallback CSV: {e}")
            return pd.DataFrame()
            
    return pd.DataFrame()

def main():
    # 1. Load DB Data (Report)
    print("Loading DB Report...")
    df_db = parse_markdown_table(ARTIFACT_REPORT_PATH)
    if df_db.empty:
        print("No data in DB Report artifact.")
        return

    # 2. Load Input Data
    print("Loading Input Data...")
    df_input = load_input_data()
    
    # 2b. Load Fallback Data (for hybrid matching)
    df_fallback = pd.DataFrame()
    if os.path.exists(FALLBACK_CSV_PATH):
        try:
             df_fallback = pd.read_csv(FALLBACK_CSV_PATH, sep=';', on_bad_lines='skip', engine='python')
             # Start normalization for fallback
             if 'Adresse' in df_fallback.columns:
                 df_fallback['norm_addr'] = df_fallback['Adresse'].apply(normalize_addr)
        except:
             pass

    if df_input.empty and df_fallback.empty:
        print("No input data found.")
        return

    print(f"Loaded DB: {len(df_db)} rows")
    print(f"Loaded Input: {len(df_input)} rows")
    print(f"Loaded Fallback: {len(df_fallback)} rows")

    # 3. Matching
    # Strategy: Iterate DB rows, find best match in Input based on Address
    
    input_addr_col = None
    if 'Adresse' in df_input.columns:
        input_addr_col = 'Adresse'
    elif 'address' in df_input.columns:
        input_addr_col = 'address'
        
    if not input_addr_col:
        # Check for Dim 2 (T) which holds address in input.md
        if 'Dim 2(T)' in df_input.columns:
            input_addr_col = 'Dim 2(T)'
        elif 'Dim 2' in df_input.columns:
            input_addr_col = 'Dim 2'
            
    if not input_addr_col:
        print("Could not identify Address column in input data. Columns:", df_input.columns)
        return

    matches = []
    
    # Pre-normalize input addresses for speed
    df_input['norm_addr'] = df_input[input_addr_col].apply(normalize_addr)
    
    # Also normalize Resk.nr(T) if valid
    if 'Resk.nr(T)' in df_input.columns:
         df_input['norm_vendor'] = df_input['Resk.nr(T)'].astype(str).apply(normalize_addr)
    
    print(f"Matching {len(df_db)} DB records against Input & Fallback...")
        # Strategy 3: Multi-Stage Advanced Matching
        
    # Helper to get all useful text from a row
    def get_row_text(r, cols):
        parts = []
        for c in cols:
            val = r.get(c)
            if pd.notna(val):
                parts.append(str(val))
        return " ".join(parts)

    
    # Helper for tokenization
    def get_tokens(s):
        if not isinstance(s, str): return set()
        # Normalize: lowercase, remove punctuation. Keep numbers!
        s = s.lower().replace(",", " ").replace(".", " ").replace("-", " ")
        return set([w for w in s.split() if w])

    # Helper for token validation
    def is_valid_token(t):
        if t.isdigit(): return True
        if len(t) > 2: return True
        return False

    stops = {'as', 'drift', 'eiendom', 'kommune', 'husleie', 'avd', 'leie', 'vei', 'gate', 'gt', 'vn', 'veien', 'nr', 'bygg', 'oss', 'og', 'for', 'i', 'på', 'til'}

    print(f"Matching {len(df_db)} DB records against Input & Fallback...")

    for idx, row in df_db.iterrows():
        db_addr = normalize_addr(row.get('Adresse', ''))
        if not db_addr or db_addr == 'n/a': continue
        
        db_name_tokens = get_tokens(row.get('Eiendom', '')) - stops
        db_addr_tokens = get_tokens(row.get('Adresse', '')) - stops
        
        db_name_tokens = {t for t in db_name_tokens if is_valid_token(t)}
        db_addr_tokens = {t for t in db_addr_tokens if is_valid_token(t)}

        # 1. Exact Name/Address Match (Normalized)
        # 2. Strong Fuzzy Token Match (Current)
        # 3. Relaxed Substring Match (New for "More Thorough")
        
        match_found = None
        source = ""
        score = 0.0
        details = ""

        # Define search targets
        targets = [
            (df_input, 'Input', ['Dim 2(T)', 'Resk.nr(T)', 'Avdeling(T)']),
            (df_fallback, 'Fallback', ['Adresse'])
        ]
        
        for df_target, src_name, search_cols in targets:
            if df_target.empty: continue
            if match_found: break # Stop if found in higher priority source
            
            # --- Stage 1: Exact Normalized Match ---
            # Try to match DB Address exactly against target normalized address
            exact_matches = df_target[df_target['norm_addr'] == db_addr]
            if not exact_matches.empty:
                best_row = exact_matches.iloc[0]
                match_found = best_row
                source = src_name
                score = 1.0
                details = "Exact Address Match"
                break
                
            # --- Stage 2: Strong Token Match (Previous Logic Refined) ---
            # Re-use logical block but optimized
            
            search_tokens = list(db_name_tokens.union(db_addr_tokens))
            if not search_tokens: continue
            
            search_tokens.sort(key=len, reverse=True)
            required_tokens = search_tokens[:3] # Must contain at least one of these
            
            if not required_tokens: continue
            regex = "|".join([re.escape(t) for t in required_tokens])
            
            # Pre-filter
            mask = pd.Series(False, index=df_target.index)
            # Check primary search col first (Name/Dim 2) or Addr
            primary_col = search_cols[0] if search_cols else 'norm_addr'
            
            if primary_col in df_target.columns:
                 mask |= df_target[primary_col].astype(str).str.contains(regex, case=False, na=False, regex=True)
            
            candidates = df_target[mask]
            
            best_c_score = 0.0
            best_c_row = None
            
            for idx_c, row_c in candidates.head(50).iterrows(): # Limit deep scan
                 # Text Construction
                 cand_text = get_row_text(row_c, search_cols)
                 cand_tokens = get_tokens(cand_text) - stops
                 
                 # Score
                 common = db_name_tokens.union(db_addr_tokens).intersection(cand_tokens)
                 # Denom: length of DB tokens (we want to find DB concept in Input)
                 target_len = len(db_name_tokens.union(db_addr_tokens))
                 if target_len == 0: continue
                 
                 ratio = len(common) / target_len
                 
                 if ratio > best_c_score:
                     best_c_score = ratio
                     best_c_row = row_c
            
            # Threshold for Stage 2
            if best_c_score > 0.60: # Sligthly lower threshold for "Thorough"
                match_found = best_c_row
                source = src_name
                score = best_c_score
                details = f"Strong Token Match ({best_c_score:.2f})"
                break
                
            # --- Stage 3: Relaxed Substring Match ---
            # DB Property Name is substring of Input text?
            # e.g. "Furene 8" in "Leieavtale Furene 8, Volda"
            
            # Only if DB Name is descriptive enough (> 5 chars)
            db_eie = str(row.get('Eiendom', '')).strip()
            if len(db_eie) > 5:
                # Escape for regex
                safe_name = re.escape(db_eie)
                # Look in primary col
                sub_mask = df_target[primary_col].astype(str).str.contains(safe_name, case=False, na=False)
                if sub_mask.any():
                    best_row = df_target[sub_mask].iloc[0] # Take first
                    match_found = best_row
                    source = src_name
                    score = 0.90 # High confidence if explicit substring
                    details = "Substring Name Match"
                    break

        if match_found is not None:
             r = match_found
             # Extract address for display
             if source == 'Input':
                 raw_val = r.get('Dim 2(T)')
                 disp_addr = str(raw_val) if pd.notna(raw_val) else "N/A"
             else:
                 raw_val = r.get('Adresse')
                 disp_addr = str(raw_val) if pd.notna(raw_val) else "N/A"
                 
             matches.append({
                 'DB_ID': row.get('Kontrakt ID'),
                 'DB_Eiendom': row.get('Eiendom'),
                 'DB_Adresse': row.get('Adresse'),
                 'Input_Adresse': disp_addr,
                 'Score': f"{score:.2f}",
                 'Input_Details': f"Source: {source} ({details}) | " + str(r.to_dict())[:200],
                 'Raw_Data': r.to_dict()
             })

    # 4. Generate Output Report
    md_output = f"# Data Correlation Report\n\n"
    md_output += f"Total Matches Found: {len(matches)}\n\n"
    md_output += "| Source | DB Eiendom | DB Adresse | Input Adresse | Score | Input Details |\n"
    md_output += "| --- | --- | --- | --- | --- | --- |\n"
    
    for m in matches:
        md_output += f"| {m['Input_Details'].split('|')[0].strip()} | {m['DB_Eiendom']} | {m['DB_Adresse']} | {m['Input_Adresse']} | {m['Score']} | {m['Input_Details']} |\n"
        
    with open(OUTPUT_PATH, 'w') as f:
        f.write(md_output)
    
    # UNMATCHED LOGGING OMITTED FOR BREVITY
        
    print(f"Report generated at {OUTPUT_PATH}")
    print(f"Matches: {len(matches)}")

    return matches

# --- Database Persistence ---

import asyncio
# Add backend to path
current_file = os.path.abspath(__file__)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file))) # .../backend
project_root = os.path.dirname(backend_dir) # .../KNOWME

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Helper to load DB URL from .env
def get_database_url():
    env_path = os.path.join(backend_dir, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip('"').strip("'")
    return os.environ.get("DATABASE_URL")

# Set Env
db_url = get_database_url()
if db_url:
    os.environ["DATABASE_URL"] = db_url

# DB Imports
try:
    from app.db.session import SessionLocal
    from app.domains.core.models.contract import Contract
    from app.domains.core.models.unit import Unit
    from app.domains.core.models.party import Party
    from app.domains.core.models.property import Property
    from app.domains.core.models.user import User
    from app.domains.hms.models.risk import RiskAssessment
    from app.domains.hms.models.internal_control import InternalControlCase
    from sqlalchemy import select
except ImportError:
    # Fallback
    from backend.app.db.session import SessionLocal
    from backend.app.domains.core.models.contract import Contract
    from backend.app.domains.core.models.unit import Unit
    from backend.app.domains.core.models.party import Party
    from backend.app.domains.core.models.property import Property
    from backend.app.domains.core.models.user import User
    from backend.app.domains.hms.models.risk import RiskAssessment
    from backend.app.domains.hms.models.internal_control import InternalControlCase
    from sqlalchemy import select

async def update_matches_in_db(matches):
    print(f"Persisting {len(matches)} matches to Database...")
    
    async with SessionLocal() as db:
        updated_count = 0
        
        for m in matches:
            contract_id = m['DB_ID']
            if not contract_id: continue
            
            # Fetch Contract
            result = await db.execute(select(Contract).where(Contract.contract_id == contract_id))
            contract = result.scalars().first()
            
            if contract:
                # Update external_data
                ext = dict(contract.external_data or {})
                if 'financials_link' not in ext:
                     ext['financials_link'] = {}
                
                # Parse input details safely
                try:
                    # It's a string repr of dict, risky but we generated it. 
                    # Let's just store the plain keys we have
                    details = m.get('Input_Details', '')
                    # Extract Source
                    source = "Input" if "Source: Input" in details else "Fallback"
                    
                    ext['financials_link'] = {
                        'matched_address': m['Input_Adresse'],
                        'score': m['Score'],
                        'source': source,
                        'description': details[:200] 
                    }
                    
                    # Store FULL Financial Data ("Update Økonomi")
                    if 'Raw_Data' in m:
                        # Clean raw data (handle NaNs before storage if not already done, though main loop does some)
                        # Actually 'Raw_Data' in matches is a dict.
                        # We need to sanitize it again just in case (pandas NaNs)
                        clean_fins = {}
                        for k, v in m['Raw_Data'].items():
                            if pd.notna(v):
                                clean_fins[k] = str(v)
                            else:
                                clean_fins[k] = None
                        
                        # --- Parse Amount for Frontend Stats ---
                        # Column: 'Kontantbeløp' (e.g. "22319,25")
                        amount_val = 0.0
                        raw_amount = m['Raw_Data'].get('Kontantbeløp')
                        if pd.notna(raw_amount):
                            try:
                                # Replace comma with dot, remove spaces
                                s_amount = str(raw_amount).replace('.', '').replace(',', '.').strip()
                                amount_val = float(s_amount)
                            except ValueError:
                                amount_val = 0.0
                        
                        clean_fins['total_spend_csv'] = amount_val
                        clean_fins['transaction_count'] = 1 # One row = one transaction
                        
                        ext['financials'] = clean_fins
                        
                        # --- Propagate to Property ---
                        # Fetch Property via Units
                        # Contract has unit_id -> Unit -> property_id -> Property
                        if contract.unit_id:
                            # Fetch Unit + Property
                            # We can fetch Unit and eagerly load property
                            q_u = select(Unit).where(Unit.unit_id == contract.unit_id)
                            res_u = await db.execute(q_u)
                            unit_obj = res_u.scalars().first()
                            
                            if unit_obj and unit_obj.property_id:
                                # Fetch Property
                                q_p = select(Property).where(Property.property_id == unit_obj.property_id)
                                res_p = await db.execute(q_p)
                                linked_property = res_p.scalars().first()
                                
                                if linked_property:
                                    p_ext = dict(linked_property.external_data or {})
                                    # Merge Logic
                                    p_ext['financials'] = clean_fins
                                    # Also add link info
                                    p_ext['financials_link'] = ext['financials_link']
                                    
                                    linked_property.external_data = p_ext
                                    db.add(linked_property)
                                    print(f"  -> Propagated financials to Property: {linked_property.address}")
                        else:
                             print(f"  -> Contract {contract_id} has no Unit linked.")

                    contract.external_data = ext
                    db.add(contract)
                    updated_count += 1
                except Exception as e:
                    print(f"Error updating contract {contract_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    
        await db.commit()
        print(f"Successfully updated {updated_count} contracts in DB.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true", help="Write matches to DB")
    args = parser.parse_args()
    
    # Run main logic
    matches = main() 
    
    if args.persist and matches:
        asyncio.run(update_matches_in_db(matches))

