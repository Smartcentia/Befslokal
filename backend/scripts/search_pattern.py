import asyncio
import sys
import os
import json
import re

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
import app.db.base
from app.domains.core.models.property import Property
from sqlalchemy import select, text

async def regex_search_elements():
    db = SessionLocal()
    try:
        print("--- Regex Search for 'XX/XXXXX' pattern in Property.external_data ---")
        # Postgres regex match on jsonb text representation is expensive but fine for this purpose
        stmt = text("""
            SELECT name, external_data 
            FROM properties 
            WHERE external_data::text ~ '\\d{2,4}/\\d{4,}'
            LIMIT 50
        """)
        result = await db.execute(stmt)
        rows = result.fetchall()
        
        found_any = False
        for row in rows:
            name, data = row
            data_str = json.dumps(data)
            # Find the match in python to print context
            matches = re.findall(r'\d{2,4}/\d{4,}', data_str)
            if matches:
                print(f"Property: {name}")
                print(f"  Matches: {matches}")
                # Print context around match
                for m in matches:
                    idx = data_str.find(m)
                    start = max(0, idx - 50)
                    end = min(len(data_str), idx + 50)
                    print(f"  Context: ...{data_str[start:end]}...")
                print("-" * 20)
                found_any = True
                
        if not found_any:
            print("No regex matches definition found in properties.")
            
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(regex_search_elements())
