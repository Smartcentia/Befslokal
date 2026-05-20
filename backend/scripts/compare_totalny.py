
import sys
import os
import asyncio
import csv
from sqlalchemy import select
from sqlalchemy.orm import joinedload

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

import app.db.base
from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property

def parse_currency(value_str):
    if not value_str:
        return 0.0
    clean_val = value_str.replace(" ", "").replace("\xa0", "").replace(",", ".").replace("kr", "").strip()
    try:
        return float(clean_val)
    except ValueError:
        return 0.0

async def compare_new_file():
    report_lines = ["# Assessment of totalny.txt", "", "Property Name | DB Rent | File Rent (New) | Diff | Status"]
    report_lines.append("--- | --- | --- | --- | ---")
    
    file_path = "docs/totalny.txt"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    async with SessionLocal() as db:
        # Pre-fetch DB data
        stmt = (
            select(Contract)
            .where(Contract.status == 'active')
            .options(joinedload(Contract.unit).joinedload(Unit.property))
        )
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        db_map = {}
        for c in contracts:
            if c.unit and c.unit.property:
                p_name_key = c.unit.property.name.lower().strip()
                rent = 0.0
                if isinstance(c.amount, dict):
                    rent = float(c.amount.get('amount_per_year', 0.0))
                db_map[p_name_key] = rent

        # Read New File
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            rent_key = None
            for key in reader.fieldnames:
                if "Kontraktsleie ved oppstart" in key:
                    rent_key = key
                    break
            
            if not rent_key:
                print("Column 'Kontraktsleie ved oppstart' not found.")
                return

            total_diff = 0.0
            mismatches = 0
            improved = 0
            
            for row in reader:
                name_raw = row.get("Avtalenavn", "").strip()
                if not name_raw:
                    continue
                
                file_rent = parse_currency(row.get(rent_key, "0"))
                
                # Retrieve from DB
                db_rent = db_map.get(name_raw.lower(), None)
                
                if db_rent is None:
                    status = "NOT IN DB"
                    diff_str = "-"
                else:
                    diff = db_rent - file_rent
                    total_diff += abs(diff)
                    if abs(diff) > 1.0:
                        status = "MISMATCH"
                        mismatches += 1
                        
                        # Check if this looks like a "fixed" mismatch
                        # i.e., File is now sane (e.g. < 100M) where it might have been crazy before?
                        # We don't have the old file here, but we know DB is sane.
                        # If File is Sane and DB is Sane, but they differ -> Genuine Mismatch
                        # If File is INSANE (>100M) -> File still bad.
                        
                        if file_rent > 100_000_000:
                            status = "FILE BAD (>100M)"
                    else:
                        status = "MATCH"
                
                if status != "MATCH":
                    report_lines.append(f"{name_raw} | {db_rent} | {file_rent} | {diff if db_rent is not None else '-'} | {status}")

            summary = [
                "",
                "## Summary",
                f"- Total Mismatches: {mismatches}",
                f"- Data Validity: {'GOOD' if mismatches < 10 else 'NEEDS REVIEW'}"
            ]
            
            final_report = "\n".join(report_lines + summary)
            
            with open("docs/totalny_assessment.md", "w") as out:
                out.write(final_report)
            
            print("Assessment complete. Report written to docs/totalny_assessment.md")

if __name__ == "__main__":
    asyncio.run(compare_new_file())
