
import sys
import os
import asyncio
import csv
import re
from sqlalchemy import select

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit

def parse_currency(value_str):
    if not value_str:
        return 0.0
    # Clean: "1 560 000" -> 1560000.0
    clean_val = value_str.replace(" ", "").replace("\xa0", "").replace(",", ".").replace("kr", "").strip()
    try:
        return float(clean_val)
    except ValueError:
        return 0.0

from sqlalchemy.orm import joinedload

async def analyze_rent():
    report_lines = ["Property Name | DB Rent (Annual) | File Rent (Start) | Diff | Match Status"]
    report_lines.append("--- | --- | --- | --- | ---")
    
    file_path = "docs/total.txt"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    async with SessionLocal() as db:
        # Pre-fetch all active contracts with property info using eager loading
        stmt = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        # Build map: Property Name -> Contract Amount
        # Note: Contract linked to Unit linked to Property. 
        # For simplicity, we assume 1 contract per property or sum if multiple.
        # But import logic created 1 active contract per unit per property.
        
        db_rent_map = {}
        for c in contracts:
            if c.unit and c.unit.property:
                p_name = c.unit.property.name.lower().strip()
                amount_data = c.amount if isinstance(c.amount, dict) else {}
                rent = amount_data.get('amount_per_year', 0.0)
                if not rent:
                    rent = 0.0
                else:
                     # Ensure it's float
                     try:
                         rent = float(rent)
                     except:
                         rent = 0.0
                
                # Handle potential duplicate names by summing? Or just logging?
                # Let's map by name. If duplicate, we might overwrite, which is a risk.
                # Better: List of contracts
                if p_name not in db_rent_map:
                    db_rent_map[p_name] = 0.0
                db_rent_map[p_name] += rent

        print(f"Loaded {len(db_rent_map)} properties with active contracts from DB.")

        # Read File
        with open(file_path, 'r', encoding='utf-8') as f:
            # Detect dialect? It looks like tab separated
            reader = csv.DictReader(f, delimiter='\t')
            
            # Normalize headers keys
            # The file has "Kontraktsleie ved oppstart (per år)"
            # Let's find the specific key from reader.fieldnames
            rent_key = None
            for key in reader.fieldnames:
                if "Kontraktsleie ved oppstart" in key:
                    rent_key = key
                    break
            
            if not rent_key:
                print("Could not find 'Kontraktsleie ved oppstart' column in file.")
                print(f"Columns found: {reader.fieldnames}")
                return

            print(f"Using column '{rent_key}' for File Rent.")

            c = 0
            for row in reader:
                name_raw = row.get("Avtalenavn", "").strip()
                if not name_raw:
                    continue
                
                # Normalize name for matching
                # The DB names might be slightly different.
                # We used "Avtalenavn" or "Lokalisering" in import.
                # Let's try direct match first.
                
                name_key = name_raw.lower()
                
                # Extract file rent
                file_rent_str = row.get(rent_key, "0")
                file_rent = parse_currency(file_rent_str)
                
                # Find in DB
                db_rent = db_rent_map.get(name_key)
                
                # If not found, try fuzzy or alternate key (Lokalisering)
                if db_rent is None:
                    # Try matching by scanning aliases?
                    # For now just verify direct hits to gauge quality
                    # Or try 'Lokalisering'
                    loc = row.get("Lokalisering", "").strip().lower()
                    if loc in db_rent_map:
                        db_rent = db_rent_map[loc]
                    else:
                        # Try finding a name in DB that contains this name or vice versa
                        # Simple substring scan
                        found = False
                        for db_name, val in db_rent_map.items():
                            if name_key in db_name or db_name in name_key:
                                db_rent = val
                                found = True
                                break
                        if not found:
                             db_rent = "N/A"

                match_status = "OK"
                diff = 0.0
                
                if db_rent != "N/A":
                    try:
                        diff = db_rent - file_rent
                        if abs(diff) > 1.0: # Tolerance
                            match_status = "MISMATCH"
                        else:
                            match_status = "MATCH"
                    except:
                        match_status = "ERROR"
                else:
                    match_status = "NOT IN DB"
                
                # Filter for interesting lines (Mismatches or Not in DB)
                # Warning: outputting everything might be huge.
                # User wants a report.
                
                db_rent_display = f"{db_rent:,.2f}" if isinstance(db_rent, float) else str(db_rent)
                file_rent_display = f"{file_rent:,.2f}"
                diff_display = f"{diff:,.2f}" if isinstance(diff, float) else "-"
                
                report_lines.append(f"{name_raw} | {db_rent_display} | {file_rent_display} | {diff_display} | {match_status}")
                c+=1

    # Write Report
    out_file = "docs/rent_discrepancy_report.md"
    with open(out_file, "w", encoding='utf-8') as f:
        for line in report_lines:
            f.write(line + "\n")
    
    print(f"Analysis complete. Report written to {out_file}")

if __name__ == "__main__":
    try:
        asyncio.run(analyze_rent())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
