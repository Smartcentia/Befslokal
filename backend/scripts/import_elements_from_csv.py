import asyncio
import sys
import os
import csv
import re

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
import app.db.base # Register all models
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

def parse_elements_id(filename):
    match = re.match(r'^(\d{2})-(\d+)-', filename)
    if match:
        year_short = match.group(1)
        seq = match.group(2)
        return f"20{year_short}/{seq}"
    return None

def normalize_address(addr):
    if not addr:
        return ""
    # Remove city part if comma exists
    addr = addr.split(',')[0]
    # Lowercase
    addr = addr.lower().strip()
    return addr

async def import_elements():
    db = SessionLocal()
    try:
        csv_path = os.path.join(os.getcwd(), 'backend', 'docs', 'Eiendom.csv')
        print(f"Reading {csv_path}...")
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
            
        print(f"Loaded {len(rows)} rows from CSV.")
        
        # Pre-load all properties to memory for smarter matching in Python
        # (avoiding complex SQL ILIKE combinations)
        stmt = select(Contract).join(Contract.unit).join(Unit.property).options(
            joinedload(Contract.unit).joinedload(Unit.property)
        )
        result = await db.execute(stmt)
        all_contracts = result.scalars().all()
        
        updates_made = 0
        matches_found = 0
        
        for row in rows:
            # Column names from Eiendom.csv
            elements_id = row.get("Elements ") # Note space at end
            csv_addr_raw = row.get("Adresselinje 1")
            
            if not elements_id or not csv_addr_raw:
                continue
                
            elements_id = elements_id.strip()
            # Handle multiple IDs if necessary, or just take as is.
            # detailed cleaning can be added if needed.
            
            csv_addr_norm = normalize_address(csv_addr_raw)
            
            # Find best match in DB contracts
            best_match = None
            
            for c in all_contracts:
                prop = c.unit.property
                db_addr_norm = normalize_address(prop.address)
                
                # Logic:
                # 1. Exact match
                # 2. CSV address starts with DB address (CSV: "Street 1B", DB: "Street 1")
                # 3. DB address starts with CSV address (CSV: "Street 1", DB: "Street 1B")
                
                if not db_addr_norm: 
                    continue
                    
                match = False
                if csv_addr_norm == db_addr_norm:
                    match = True
                elif csv_addr_norm.startswith(db_addr_norm):
                    match = True
                elif db_addr_norm.startswith(csv_addr_norm):
                     match = True
                     
                if match:
                    best_match = c
                    break # Take first good match
            
            # --- Financial Parsing ---
            def parse_currency(value):
                if not value:
                    return 0.0
                # Remove spaces, "kr", etc.
                clean = str(value).replace("kr", "").replace(" ", "").replace("\xa0", "").replace(",", ".")
                try:
                    return float(clean)
                except ValueError:
                    return 0.0

            # 1. Rent (KPI adjusted or startup)
            rent_kpi = parse_currency(row.get("KPI-justert kontraktsleie til okt 2025"))
            rent_startup = parse_currency(row.get("Kontraktsleie ved oppstart (per år)"))
            rent_annual = rent_kpi if rent_kpi > 0 else rent_startup

            # Debug specific properties
            if "kaigata" in csv_addr_norm or "brennstadmoen" in csv_addr_norm:
                 print(f"DEBUG {csv_addr_raw}:")
                 print(f"   KPI Rent Raw: '{row.get('KPI-justert kontraktsleie til okt 2025')}' -> Parsed: {rent_kpi}")
                 print(f"   Startup Rent Raw: '{row.get('Kontraktsleie ved oppstart (per år)')}' -> Parsed: {rent_startup}")
                 print(f"   Final Annual Rent: {rent_annual}")
                 if not best_match:
                     print(f"   WARNING: No DB match found for {csv_addr_raw}!")
                 else:
                     print(f"   Matched DB Contract: {best_match.contract_id} (Current Amount: {best_match.amount.get('amount_per_year') if best_match.amount else 'None'})")

            
            # 2. Maintenance (Property level)
            maintenance_cost = parse_currency(row.get("Indre vedlikehold"))
            
            # 3. Specific Costs (Contract level)
            caretaker = parse_currency(row.get("Vaktmestertjenester kr per år"))
            cleaning = parse_currency(row.get("Renhold pr år"))
            parking = parse_currency(row.get("Parkeringsleie kr per år"))
            card_reader = parse_currency(row.get("Kost kortleser"))

            # --- Database Updates ---
            if best_match:
                matches_found += 1
                prop = best_match.unit.property
                modified = False
                
                # Update Elements ID
                if elements_id and best_match.elements != elements_id:
                    print(f"UPDATING ID {best_match.contract_id} ({prop.name}): {best_match.elements} -> {elements_id}")
                    best_match.elements = elements_id
                    modified = True

                # Update Financials (Contract)
                # Ensure amount is a dict
                current_amount = dict(best_match.amount) if best_match.amount else {}
                # Only update if we have a non-zero value from CSV, 
                # OR if the DB value is None (to initialize it). 
                # Avoid overwriting existing valid data with 0.0 from a secondary CSV row.
                if rent_annual > 0:
                    if current_amount.get("amount_per_year") != rent_annual:
                       print(f"   Updating Rent: {current_amount.get('amount_per_year')} -> {rent_annual}")
                       current_amount["amount_per_year"] = rent_annual
                       best_match.amount = current_amount
                       modified = True
                
                # Update Specific Costs 
                # Same logic: only overwrite if we have a value.
                if caretaker > 0 and best_match.caretaker_cost != caretaker:
                    best_match.caretaker_cost = caretaker
                    modified = True
                if cleaning > 0 and best_match.cleaning_cost != cleaning:
                    best_match.cleaning_cost = cleaning
                    modified = True
                if parking > 0 and best_match.parking_cost != parking:
                    best_match.parking_cost = parking
                    modified = True
                if card_reader > 0 and best_match.card_reader_cost != card_reader:
                    best_match.card_reader_cost = card_reader
                    modified = True

                # Update Property Maintenance (External Data)
                # We need to explicitly fetch and update property to ensure session tracks it
                if maintenance_cost > 0:
                     ext_data = dict(prop.external_data) if prop.external_data else {}
                     fin_data = ext_data.get("financials", {})
                     
                     if fin_data.get("total_maintenance") != maintenance_cost:
                         print(f"   Updating Property Maintenance ({prop.name}): {fin_data.get('total_maintenance')} -> {maintenance_cost}")
                         fin_data["total_maintenance"] = maintenance_cost
                         ext_data["financials"] = fin_data
                         prop.external_data = ext_data
                         db.add(prop) # Explicitly mark property for update
                         modified = True

                if modified:
                    db.add(best_match)
                    updates_made += 1
                else:
                    print(f"SKIPPING {best_match.contract_id}: Data already up to date.")

            else:
                # Debug failed matches for potentially better logic
                print(f"NO MATCH for '{csv_addr_raw}' (ID: {elements_id})")

        await db.commit()
        print(f"\nMigration Complete.")
        print(f"Matches found: {matches_found}")
        print(f"Contracts updated: {updates_made}")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(import_elements())
