import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy import inspect

# Enforce backend directory as CWD so imports work
if os.getcwd().endswith("backend"):
    sys.path.append(os.getcwd())
else:
    # If strictly running from deeper or elsewhere, try adding common root
    sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.db.session import SessionLocal

async def main():
    async with SessionLocal() as session:
        print("--- Database Inspection ---")
        
        # 1. List Tables
        print("\n[ Tables ]")
        try:
             # Async inspection is tricky directly, simpler to just run raw SQL for table names in Postgres
             result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
             tables = [row[0] for row in result.fetchall()]
             for t in tables:
                 print(f" - {t}")
        except Exception as e:
            print(f"Error listing tables: {e}")
            return

        # 2. Count Rows in Main Tables
        print("\n[ Row Counts ]")
        count_queries = {
            "Contracts": "SELECT COUNT(*) FROM contracts",
            "Properties": "SELECT COUNT(*) FROM properties",
            "Units": "SELECT COUNT(*) FROM units",
            "Parties": "SELECT COUNT(*) FROM parties",
            "Files": "SELECT COUNT(*) FROM file_meta",
            "Risk Assessments": "SELECT COUNT(*) FROM risk_assessments"
        }

        for label, query in count_queries.items():
            try:
                # Check if table exists first (simple check)
                table_name = query.split()[-1]
                if table_name in tables:
                    res = await session.execute(text(query))
                    count = res.scalar()
                    print(f"{label:<20}: {count}")
                else:
                    print(f"{label:<20}: Table {table_name} not found")
            except Exception as e:
                print(f"{label:<20}: Error ({e})")

        # 3. Sample Date (First 3 Contracts)
        print("\n[ Sample Contracts ]")
        try:
            # Select only existing columns. contract_number is inside external_data
            res = await session.execute(text("SELECT contract_id, status, external_data FROM contracts LIMIT 3"))
            rows = res.fetchall()
            if not rows:
                print("No contracts found.")
            for row in rows:
                c_id, status, ext_data = row
                c_number = "N/A"
                if ext_data and isinstance(ext_data, dict):
                    c_number = ext_data.get("contract_number", "N/A")
                
                print(f"ID: {c_id} | Status: {status} | Number: {c_number}")
        except Exception as e:
             print(f"Error fetching sample: {e}")

if __name__ == "__main__":
    asyncio.run(main())
