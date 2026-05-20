import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
try:
    from app.domains.core.models.file import File
except ImportError:
    # If file model file is not found/named differently, try generic import or raw sql
    # But based on contract.py it should exist. Let's assume standard structure or check if we fail.
    pass

from sqlalchemy import select, text

async def inspect_filenames():
    db = SessionLocal()
    try:
        print("--- Inspecting Contract Filenames ---")
        # Raw SQL might be safer if we are unsure of File model path
        stmt = text("""
            SELECT c.contract_id, f.filename 
            FROM contracts c
            JOIN files f ON c.contract_id = f.contract_id
            LIMIT 50
        """)
        result = await db.execute(stmt)
        rows = result.fetchall()
        
        matches = 0
        for row in rows:
            cid, fname = row
            # Check for pattern like digit/digit
            if any(char.isdigit() for char in fname) and '/' in fname:
                 print(f"Contract {cid}: Filename '{fname}' might contain ID")
                 matches += 1
            elif "sak" in fname.lower() or "arkiv" in fname.lower():
                 print(f"Contract {cid}: Filename '{fname}' contains keyword")
                 matches += 1
            else:
                 # Print a few random ones just to see format
                 if matches < 5:
                     print(f"Contract {cid}: Filename '{fname}'")

        if matches > 0:
            print(f"\nFound {matches} potentially relevant filenames.")
        else:
             print("\nNo obvious ID patterns (like '/') found in filenames.")

    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(inspect_filenames())
