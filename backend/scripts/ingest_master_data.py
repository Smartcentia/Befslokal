
import pandas as pd
import os
import chardet
import csv
import json
import hashlib
from typing import List, Dict, Any, Optional

class IngestEngine:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.log = []

    def log_event(self, event: str, details: Any):
        print(f"[{event}] {details}")
        self.log.append({"event": event, "details": details, "timestamp": pd.Timestamp.now().isoformat()})

    def detect_format(self, file_path: str):
        # Since standard open might fail, we try a tiered approach
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)
                result = chardet.detect(raw_data)
                encoding = result['encoding'] or 'utf-8'
                
                # Check for delimiter
                content = raw_data.decode(encoding)
                if ';' in content and ',' not in content:
                    delimiter = ';'
                elif ',' in content:
                    delimiter = ','
                else:
                    delimiter = ',' # Default
                
                return encoding, delimiter
        except Exception as e:
            # Fallback for protected files if the above fails
            # In regular Python this would fail if open() fails, 
            # but we're banking on the agent context or the user fixing permissions.
            return 'utf-8-sig', ','

    def read_csv_robustly(self, file_path: str, skip_rows: int = 0):
        encoding, delimiter = self.detect_format(file_path)
        
        try:
            df = pd.read_csv(file_path, encoding=encoding, sep=delimiter, skiprows=skip_rows)
            # Cleanup columns
            df.columns = [str(c).strip() for c in df.columns]
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            
            self.log_event("READ_SUCCESS", {
                "file": os.path.basename(file_path),
                "rows": len(df),
                "cols": list(df.columns),
                "encoding": encoding,
                "delimiter": delimiter
            })
            return df
        except Exception as e:
            self.log_event("READ_FAILED", {"file": file_path, "error": str(e)})
            return None

    def save_clean(self, df: pd.DataFrame, name: str):
        path = os.path.join(self.output_dir, name)
        df.to_csv(path, index=False)
        return path

# --- Specialized Cleaners ---

def clean_address_book(engine: IngestEngine, files: List[str]):
    all_dfs = []
    for f in files:
        region = os.path.basename(f).split('(')[-1].replace(').csv', '')
        df = engine.read_csv_robustly(f)
        if df is not None:
            df['source_region'] = region
            all_dfs.append(df)
    
    if not all_dfs:
        return None
        
    master_df = pd.concat(all_dfs, ignore_index=True)
    
    # Standardize columns
    col_map = {
        'Gateadresse': 'street_address_raw',
        'Poststed': 'poststed',
        'Postnummer': 'postnr',
        'Kontakt': 'contact_name_raw'
    }
    master_df = master_df.rename(columns=col_map)
    
    # Normalization
    master_df['postnr'] = master_df['postnr'].astype(str).str.zfill(4).str.replace(r'\.0$', '', regex=True)
    
    # Normalized street address: lowercase, strip secondary info after comma
    master_df['street_address_norm'] = master_df['street_address_raw'].str.lower().str.split(',').str[0].str.strip()
    
    # Normalized contact name: lowercase, remove "avd", "avdeling", punctuation
    def normalize_name(name):
        if pd.isna(name): return ""
        name = str(name).lower()
        name = name.replace('avd.', '').replace('avdeling', '').replace('-', ' ').replace('.', '')
        return " ".join(name.split())
        
    master_df['contact_name_norm'] = master_df['contact_name_raw'].apply(normalize_name)
    
    engine.save_clean(master_df, "address_book_clean.csv")
    return master_df

def clean_birk(engine: IngestEngine, file_path: str):
    # BIRK has a leading comma/blank row issue based on grep
    # We read it raw first to find the header
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            # Find the first line that looks like a header (contains region or enhet)
            header_idx = 0
            for i, line in enumerate(lines[:10]):
                if 'Region' in line or 'Enhet' in line:
                    header_idx = i
                    break
        
        df = engine.read_csv_robustly(file_path, skip_rows=header_idx)
        if df is None: return None
        
        # BIRK specific normalization
        # ... logic for birk columns ...
        
        engine.save_clean(df, "birk_clean.csv")
        return df
    except Exception as e:
        engine.log_event("BIRK_CLEAN_FAILED", str(e))
        return None

if __name__ == "__main__":
    eng = IngestEngine("backend/data/clean")
    
    # 1.2 Address Book
    addr_files = [
        "backend/docs/datafiler/Leveringsadresser til Frank Vevle(Nord).csv",
        "backend/docs/datafiler/Leveringsadresser til Frank Vevle(Midt).csv",
        "backend/docs/datafiler/Leveringsadresser til Frank Vevle(Vest).csv",
        "backend/docs/datafiler/Leveringsadresser til Frank Vevle(Sør).csv",
        "backend/docs/datafiler/Leveringsadresser til Frank Vevle(Øst).csv",
        "backend/docs/datafiler/Leveringsadresser til Frank Vevle(Bufdir).csv"
    ]
    clean_address_book(eng, addr_files)
    
    # Save log
    with open("backend/data/clean/run_log.json", "w") as f:
        json.dump(eng.log, f, indent=2)
