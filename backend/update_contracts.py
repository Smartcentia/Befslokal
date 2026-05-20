import asyncio
import csv
import sys
import os
import argparse
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from datetime import datetime

# Add the current directory to sys.path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), "app"))
# Adjust path to point to backend root if necessary
sys.path.append(os.path.dirname(__file__))

from app.db.session import SessionLocal
from app.db.base import Base # This registers all models
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property
from app.domains.core.models.party import Party

def parse_date(date_str):
    if not date_str or date_str.lower() in ["-", "ikke oppgitt"]:
        return None
    try:
        # Try DD.MM.YYYY
        return datetime.strptime(date_str, "%d.%m.%Y").isoformat()
    except ValueError:
        pass
    
    try:
        # Try Month YYYY (e.g. "Mai 2009")
        # Translation map for months if needed, but assuming simple numeric or English for now
        # Actually typical Norwegian months might be present.
        # Let's keep it simple and skip complex parsing for now unless strictly needed.
        return None 
    except:
        return None

async def main(dry_run=True):
    print(f"Connecting to database... (Dry Run: {dry_run})")
    async with SessionLocal() as db:
        if not dry_run:
            print("🔧 Disabling trigger 'tsvectorupdate_contracts' to bypass Enum bug...")
            await db.execute(text("ALTER TABLE contracts DISABLE TRIGGER tsvectorupdate_contracts"))
            await db.commit()

        # Fetch all contracts with related data
        query = select(Contract).options(
            selectinload(Contract.unit).selectinload(Unit.property),
            selectinload(Contract.party)
        )
        result = await db.execute(query)
        db_contracts = result.scalars().all()
        
        print(f"Fetched {len(db_contracts)} contracts from database.")

        # Load CSV data
        csv_path = "contracts.csv" # Provided file is in KNOWME/contracts.csv? Or backend dir?
        # User said: /Users/frank/BEFS3/KNOWME/contracts.csv
        # Script is in /Users/frank/BEFS3/KNOWME/backend/update_contracts.py
        # So ../contracts.csv
        csv_path = os.path.join(os.path.dirname(__file__), "..", "contracts.csv")
        
        if not os.path.exists(csv_path):
            print(f"Error: Could not find {csv_path}")
            return

        updates = []
        skipped = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
            print(f"Read {len(csv_rows)} rows from CSV.")

            for row in csv_rows:
                csv_contract_nr = row.get('Kontraktnr', '').strip()
                csv_address = row.get('Adresse', '').strip()
                csv_gnr_bnr = row.get('Gnr/Bnr', '').strip()
                
                matched_contract = None
                
                # Matching Logic (Same as compare_contracts.py)
                # 1. Match by Address Fuzzy
                if not matched_contract and csv_address:
                    for c in db_contracts:
                        if c.unit and c.unit.property and c.unit.property.address:
                            if csv_address.lower() in c.unit.property.address.lower() or c.unit.property.address.lower() in csv_address.lower():
                                matched_contract = c
                                break
                
                # 2. Match by Gnr/Bnr
                if not matched_contract and csv_gnr_bnr:
                     for c in db_contracts:
                        if c.unit and c.unit.property:
                            p = c.unit.property
                            if p.gnr is not None and p.bnr is not None:
                                db_gnr_bnr = f"{p.gnr}/{p.bnr}"
                                if csv_gnr_bnr == db_gnr_bnr:
                                    matched_contract = c
                                    break
                
                if matched_contract:
                    changes = []
                    
                    # Update Status
                    csv_status = row.get('Status (01.01.26)', '')
                    new_status = None
                    if "Aktiv" in csv_status:
                        new_status = "active"
                    # Update Status
                    csv_status = row.get('Status (01.01.26)', '')
                    new_status = None
                    if "Aktiv" in csv_status:
                        new_status = "active"
                    elif "UTLØPT" in csv_status or "Opphørt" in csv_status:
                        new_status = "terminated"
                    
                    if new_status and matched_contract.status != new_status:
                        changes.append(f"Status: {matched_contract.status} -> {new_status}")
                        if not dry_run:
                            # Trigger is disabled, so we can update safely.
                            # Note: We must still handle Enum casting for the UPDATE itself if we use SQL, 
                            # but since the Trigger was the one failing on COALESCE('', Enum), 
                            # the parsing of the UPDATE statement itself might be fine with explicit cast or literal.
                            await db.execute(
                                text(f"UPDATE contracts SET status = '{new_status}'::contractstatus WHERE contract_id = :id"),
                                {"id": matched_contract.contract_id}
                            )
                    csv_area_raw = row.get('Areal (m²)', '').replace(' ', '')
                    if csv_area_raw and csv_area_raw.isdigit():
                        new_area = float(csv_area_raw)
                        if matched_contract.unit:
                            # Use a small epsilon for float comparison logic, or just equality
                            current_area = matched_contract.unit.area_sqm
                            if current_area != new_area:
                                changes.append(f"Area: {current_area} -> {new_area}")
                                matched_contract.unit.area_sqm = new_area
                    
                    # Update Contract Number (External Data)
                    if csv_contract_nr:
                        if not matched_contract.external_data:
                            matched_contract.external_data = {}
                        
                        current_nr = matched_contract.external_data.get('kontraktnr')
                        if current_nr != csv_contract_nr:
                            changes.append(f"Kontraktnr: {current_nr} -> {csv_contract_nr}")
                            matched_contract.external_data['kontraktnr'] = csv_contract_nr
                            # Also flag DB as modified to ensure JSON update persists if it's the only change
                            from sqlalchemy.orm.attributes import flag_modified
                            flag_modified(matched_contract, "external_data")

                    # Update Dates (Periods)
                    start_date = parse_date(row.get('Startdato'))
                    end_date = parse_date(row.get('Sluttdato'))
                    
                    if start_date or end_date:
                        # Ensure periods is a dict, or handle list if necessary
                        if matched_contract.periods is None:
                            matched_contract.periods = {}
                            
                        # If it's a list, log it and maybe try to use the first element if strictly one, 
                        # or just convert to dict if that's the intended schema. 
                        # For safety, if it's a list, we'll try to convert it to a dict if it looks like legacy single-period
                        if isinstance(matched_contract.periods, list):
                            if len(matched_contract.periods) == 0:
                                matched_contract.periods = {}
                            elif isinstance(matched_contract.periods[0], dict):
                                # Warn about structure change but convert to flat dict for main period
                                # changes.append(f"Converting periods list to dict: {matched_contract.periods} -> {matched_contract.periods[0]}")
                                matched_contract.periods = matched_contract.periods[0]
                            else:
                                print(f"Skipping periods update for {csv_address}: Unknown list structure {matched_contract.periods}")
                                continue

                        current_start = matched_contract.periods.get('start_date')
                        current_end = matched_contract.periods.get('end_date')
                        
                        if start_date and current_start != start_date:
                            changes.append(f"Start Date: {current_start} -> {start_date}")
                            matched_contract.periods['start_date'] = start_date
                        
                        if end_date and current_end != end_date:
                            changes.append(f"End Date: {current_end} -> {end_date}")
                            matched_contract.periods['end_date'] = end_date
                            
                        if changes:
                            from sqlalchemy.orm.attributes import flag_modified
                            flag_modified(matched_contract, "periods")

                    if changes:
                        updates.append({
                            "ContractID": matched_contract.contract_id,
                            "Address": csv_address,
                            "Status": matched_contract.status, # Log status
                            "Changes": "; ".join(changes)
                        })
                        
                        if not dry_run:
                            try:
                                await db.flush()
                            except Exception as e:
                                print(f"❌ Error updating {csv_address} (ID: {matched_contract.contract_id}): {e}")
                                # Rollback or skipping this object might be tricky with session transaction
                                # But at least we see WHICH one failed.
                                # Since one failure aborts the transaction, we must break or we need nested transactions (savepoints).
                                # AsyncSession support nested transactions via begin_nested()
                                # But for now let's just crash with info.
                                raise e
                else:
                    skipped.append(csv_address or "Unknown Address")

        # Report
        print(f"\n--- Update Report (Dry Run: {dry_run}) ---")
        print(f"Matched & Updated: {len(updates)}")
        print(f"Skipped (No Match): {len(skipped)}")
        
        if updates:
            print("\nSample Updates:")
            for u in updates[:5]:
                print(f" - {u['Address']}: {u['Changes']}")
        
        if not dry_run:
            print("\nCommitting changes to database...")
            await db.commit()
            print("🔧 Re-enabling trigger 'tsvectorupdate_contracts'...")
            await db.execute(text("ALTER TABLE contracts ENABLE TRIGGER tsvectorupdate_contracts"))
            await db.commit()
            print("Done.")
        else:
            print("\nDry run completed. No changes made.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update contracts from CSV")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without committing changes")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Actually commit changes")
    parser.set_defaults(dry_run=True)
    
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
