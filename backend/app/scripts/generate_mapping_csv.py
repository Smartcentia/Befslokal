
import asyncio
import sys
import os
import re
import csv
from sqlalchemy import select

sys.path.append(os.path.join(os.getcwd(), 'backend'))
# from app.db.session import SessionLocal # Not needed for just parsing noe.txt unique names

INPUT_FILE = "backend/docs/noe.txt"
OUTPUT_CSV = "backend/docs/noe_mapping_needed.csv"

def generate_csv():
    # Extract IDs from noe.txt
    noe_map = {} # ID -> set(Names)
    
    with open(INPUT_FILE, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        match = re.search(r'^(.*?) (\d{6}) (.*) ((-?[\d]+,[\d]+)|(-?[\d]+))$', line)
        if match:
            pid = match.group(2)
            middle = match.group(3)
            if pid not in noe_map: noe_map[pid] = []
            noe_map[pid].append(middle)
            
    # Consolidate Names
    categories = [
        "Barnevernsinstitusjoner", "Fosterhjemstjenesten", "Regionale fellesfunksjoner",
        "Sentre for foreldre og barn", "Familieverntjeneste", "Omsorgssentre for mindreårige",
        "Statlig regionalt barnevernmyndighet", "Beredskapshjem", "Inntak", "Fosterhjem", "Hjelpetiltak i hjemmet"
    ]
    
    csv_rows = []
    
    for pid, middles in noe_map.items():
        sample = middles[0]
        prop_name = sample
        for cat in sorted(categories, key=len, reverse=True):
             if cat in sample:
                 prop_name = sample.split(cat)[0].strip()
                 break
        csv_rows.append([pid, prop_name, ""])
        
    # Write CSV
    with open(OUTPUT_CSV, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(['ID', 'NOE Name', 'DB Property Address (Fill This In)'])
        writer.writerows(csv_rows)
        
    print(f"Generated {OUTPUT_CSV} with {len(csv_rows)} rows.")

if __name__ == "__main__":
    generate_csv()
