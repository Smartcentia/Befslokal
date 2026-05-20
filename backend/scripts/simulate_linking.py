
import pandas as pd
import os
import re
from typing import Dict, Any, List

def simulate():
    print("=== BEFS Data Strategy Simulation ===\n")
    
    # Paths
    backend_docs = "/Users/frank/Documents/BEFS_CLEAN/backend/docs"
    ok1_path = os.path.join(backend_docs, "ok1.csv")
    totalny_path = os.path.join(backend_docs, "totalny.txt")
    contracts_path = "/Users/frank/Documents/BEFS_CLEAN/contracts.csv"
    
    # 1. Load Data
    print("Loading datasets...")
    try:
        # Transactions (ok1.csv)
        df_tx = pd.read_csv(ok1_path, sep=';', encoding='windows-1252', dtype=str)
        print(f"Loaded {len(df_tx)} transactions from ok1.csv")
        
        # Properties (totalny.txt)
        df_prop = pd.read_csv(totalny_path, sep='\t', encoding='utf-8', dtype=str)
        print(f"Loaded {len(df_prop)} properties from totalny.txt")
        
        # Enrichment (contracts.csv)
        df_contracts = pd.read_csv(contracts_path, sep=',', encoding='utf-8', dtype=str)
        print(f"Loaded {len(df_contracts)} enrichment records from contracts.csv")
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    # 2. Simulate Property Master Data (Linking Dim 1)
    # Extracting ID from "2330 - Name"
    df_prop['sim_lokalisering_id'] = df_prop['Lokalisering'].str.extract(r'^(\d+)').fillna('')
    
    # 3. Simulate Transaction Linking
    # Current matching is based on Dim 2(T) vs Name/Address
    # We want to add Dim 1 -> sim_lokalisering_id
    
    tx_to_prop = {}
    matched_count = 0
    
    print("\n--- Simulating Match Rates ---")
    
    # Sample link check
    sample_tx = df_tx.head(1000)
    for idx, row in sample_tx.iterrows():
        dim1 = row.get('Avdeling', '')
        dim2_t = row.get('Dim 2(T)', '')
        
        # Try HEURISTIC 1: Dim 1 code directly (4-digit?)
        # Let's see if any Dim 1 matches any prop ID
        if dim1 in df_prop['sim_lokalisering_id'].values:
            matched_count += 1
            continue
            
        # Try HEURISTIC 2: Original Address/Name matching (current implementation)
        # (This is more complex to simulate perfectly here without full lookup table)
        
    print(f"Preliminary Dim 1 direct match rate (Sample 1000): {matched_count/1000:.1%}")

    # 4. Simulate Rebooking Heuristic (H1, H2)
    # Scan for "Beskrivelse" - Wait, ok1.csv doesn't have it?
    # Let's check for any text-like columns
    possible_text_cols = [c for c in df_tx.columns if 'T' in c or 'Beskrivelse' in c or 'Tekst' in c]
    print(f"\nPossible text columns in ok1.csv: {possible_text_cols}")
    
    # 5. Simulate Enrichment
    print("\n--- Simulating Data Enrichment ---")
    # Match contracts to properties by Address
    enriched_props = 0
    for idx, prop in df_prop.head(10).iterrows():
        addr = str(prop.get('Adresse og Postnummer ', '')).lower()
        if addr:
             # Find in contracts
             matches = df_contracts[df_contracts['Adresse'].str.lower().str.contains(addr, na=False)]
             if not matches.empty:
                 enriched_props += 1
                 print(f"Enriched: {prop['Lokalisering']} with capacity/owner from contracts.csv")
                 
    print(f"Successfully enriched {enriched_props} out of 10 sample properties.")

if __name__ == "__main__":
    simulate()
