import asyncio
import csv
import sys
import os
from sqlalchemy import select
from sqlalchemy.orm import selectinload

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

async def main():
    print("Connecting to database...")
    async with SessionLocal() as db:
        # Fetch all contracts with related data
        query = select(Contract).options(
            selectinload(Contract.unit).selectinload(Unit.property),
            selectinload(Contract.party)
        )
        result = await db.execute(query)
        db_contracts = result.scalars().all()
        
        print(f"Fetched {len(db_contracts)} contracts from database.")

        # Load CSV data
        csv_path = "../contracts.csv"
        if not os.path.exists(csv_path):
            print(f"Error: Could not find {csv_path}")
            return

        comparisons = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_rows = list(reader)
            print(f"Read {len(csv_rows)} rows from CSV.")

            for row in csv_rows:
                csv_contract_nr = row.get('Kontraktnr', '').strip()
                csv_address = row.get('Adresse', '').strip()
                csv_gnr_bnr = row.get('Gnr/Bnr', '').strip()
                
                matched_contract = None
                match_type = "No Match"

                # 1. Try matching by Contract Number (if requested features are implemented, otherwise skip)
                # Assuming external_data might hold the contract number if it was imported previously
                # but for now we might rely on Address fuzzy match or strict string match if stored.
                
                # 2. Try strict match on Address
                if not matched_contract and csv_address:
                    for c in db_contracts:
                        if c.unit and c.unit.property and c.unit.property.address:
                            # Simple normalization
                            if csv_address.lower() in c.unit.property.address.lower() or c.unit.property.address.lower() in csv_address.lower():
                                matched_contract = c
                                match_type = "Address Fuzzy"
                                break
                
                # 3. Try matching by Gnr/Bnr
                if not matched_contract and csv_gnr_bnr:
                     for c in db_contracts:
                        if c.unit and c.unit.property:
                            p = c.unit.property
                            # Construct DB Gnr/Bnr string
                            if p.gnr is not None and p.bnr is not None:
                                db_gnr_bnr = f"{p.gnr}/{p.bnr}"
                                if csv_gnr_bnr == db_gnr_bnr:
                                    matched_contract = c
                                    match_type = "Gnr/Bnr"
                                    break

                # Prepare Comparison Record
                comp_base = {
                    "CSV_Kontraktnr": csv_contract_nr,
                    "CSV_Adresse": csv_address,
                    "Match_Type": match_type,
                    "DB_ID": str(matched_contract.contract_id) if matched_contract else "N/A"
                }

                if matched_contract:
                    # Compare specific fields
                    # Property Address
                    db_address = matched_contract.unit.property.address if matched_contract.unit and matched_contract.unit.property else "N/A"
                    comparisons.append({**comp_base, "Field": "Address", "CSV_Value": csv_address, "DB_Value": db_address, "Status": "Match" if csv_address.lower() == db_address.lower() else "Mismatch"})
                    
                    # Status
                    csv_status = row.get('Status (01.01.26)', '')
                    db_status = matched_contract.status or "N/A"
                    # CSV uses "🟢 Aktiv", DB likely "active"
                    normalized_csv_status = "active" if "Aktiv" in csv_status else "terminated" if "UTLØPT" in csv_status or "Opphørt" in csv_status else csv_status
                    # normalized_db_status = db_status.lower()
                    comparisons.append({**comp_base, "Field": "Status", "CSV_Value": csv_status, "DB_Value": db_status, "Status": "Match" if normalized_csv_status == db_status else "Mismatch"})

                    # Area
                    csv_area = row.get('Areal (m²)', '').replace(' ', '')
                    db_area = str(matched_contract.unit.area_sqm) if matched_contract.unit and matched_contract.unit.area_sqm else "N/A"
                     # Simple check
                    comparisons.append({**comp_base, "Field": "Area", "CSV_Value": csv_area, "DB_Value": db_area, "Status": "Check Manual" if csv_area != db_area else "Match"})

                    # Dates
                    csv_start = row.get('Startdato', '')
                    csv_end = row.get('Sluttdato', '')
                    # TODO: Parse DB dates to string for comparison
                    # comparisons.append({**comp_base, "Field": "StartDate", "CSV_Value": csv_start, "DB_Value": "TODO", "Status": "Info"})

                else:
                    comparisons.append({**comp_base, "Field": "All", "CSV_Value": "N/A", "DB_Value": "N/A", "Status": "Not Found in DB"})
        
        # Write Report
        report_file = "comparison_report.csv"
        keys = ["CSV_Kontraktnr", "CSV_Adresse", "Match_Type", "DB_ID", "Field", "CSV_Value", "DB_Value", "Status"]
        with open(report_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(comparisons)
            
        print(f"Comparison report written to {report_file}")

if __name__ == "__main__":
    asyncio.run(main())
