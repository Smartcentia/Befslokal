
import csv
import sys
import os
from difflib import SequenceMatcher

# Paths
SYSTEM_CSV = "/Users/frank/BEFS3/KNOWME/backend/data/csv_portfolio_data.csv"
MASTER_CSV = "/Users/frank/BEFS3/KNOWME/backend/docs/Eiendomsportefølje_ 2025.csv"

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def load_system_data(path):
    data = []
    with open(path, mode='r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader, None)
        # Headers: #;Region;Filnavn (Kilde);...
        # Index 5: Adresse, Index 7: Areal (m²)
        for row in reader:
            if not row: continue
            try:
                name = row[2] # Filnavn/Name approximation
                addr = row[5]
                area = row[7].replace(" ", "").replace(",", ".")
                cat = row[4]
                data.append({
                    "name": name,
                    "address": addr,
                    "area": area,
                    "row_raw": row
                })
            except IndexError:
                continue
    return data

def load_master_data(path):
    data = []
    with open(path, mode='r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader, None)
        # Index 1: Avtalenavn (Name), Index 11: Adresselinje 1, Index 15: Areal
        for row in reader:
            if not row: continue
            try:
                name = row[1]
                addr = row[11]
                area = row[15].replace(" ", "").replace(",", ".")
                data.append({
                    "name": name,
                    "address": addr,
                    "area": area,
                    "row_raw": row
                })
            except IndexError:
                continue
    return data

def main():
    print("Loading data...")
    system_props = load_system_data(SYSTEM_CSV)
    master_props = load_master_data(MASTER_CSV)
    
    print(f"System Properties: {len(system_props)}")
    print(f"Master Properties: {len(master_props)}")

    # Analysis 1: Find Ghosts (In System but NOT in Master)
    print("\n--- ANALYSIS 1: POTENTIAL GHOSTS (In System, Not in Master) ---")
    ghosts = []
    for sys_p in system_props:
        match_found = False
        best_score = 0
        best_match = None
        
        # Try finding a match in Master
        for mast_p in master_props:
            # Check address similarity
            score_addr = similarity(sys_p['address'].lower(), mast_p['address'].lower())
            # Check name similarity
            score_name = similarity(sys_p['name'].lower(), mast_p['name'].lower())
            
            # If address matches well, it's a match
            if score_addr > 0.85:
                match_found = True
                break
            
            # Tracking best guess
            if score_addr > best_score:
                best_score = score_addr
                best_match = mast_p

        if not match_found:
            ghosts.append(sys_p)
            print(f"[GHOST?] {sys_p['name'][:30]}... | Addr: {sys_p['address']} | Best Match: {best_score:.2f} ({best_match['address'] if best_match else 'None'})")

    # Analysis 2: Data Gaps (In System, Missing Area, But Available in Master)
    print("\n--- ANALYSIS 2: ENRICHMENT OPPORTUNITIES (Missing Area in System, Found in Master) ---")
    for sys_p in system_props:
        # Check if Area is missing or zero-ish
        try:
            area_val = float(sys_p['area'])
        except ValueError:
            area_val = 0
            
        if area_val < 1:
            # Find in master
            for mast_p in master_props:
                score_addr = similarity(sys_p['address'].lower(), mast_p['address'].lower())
                if score_addr > 0.85:
                    master_area = mast_p['area']
                    try:
                        ma_val = float(master_area)
                        if ma_val > 1:
                             print(f"[FIXABLE] {sys_p['name'][:30]}... | System Area: {sys_p['area']} -> Master Area: {master_area} | Addr: {sys_p['address']}")
                    except:
                        pass
                    break

if __name__ == "__main__":
    main()
