
import sys
import os
import asyncio
from sqlalchemy import select, update

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

# Import base to ensure all models are registered
import app.db.base 

from app.db.session import SessionLocal
from app.domains.core.models.property import Property

MAPPING = {
    # Legacy strings
    "VEST": "Vest",
    "ØST": "Øst",
    "SØR": "Sør",
    "Region Øst": "Øst",
    "Region Vest": "Vest",
    "Region Sør": "Sør",
    "Region Nord": "Nord",
    "Region Midt": "Midt-Norge",
    
    # Legacy numbered strings (Cleaning up these to plain names)
    "01 - Nord": "Nord",
    "01 - Nordland": "Nord",
    "01-Nordland": "Nord",
    "02 - Midt-Norge": "Midt-Norge",
    "02 - Midt": "Midt-Norge",
    "02 - Troms og Finnmark": "Nord",
    "03 - Trøndelag": "Midt-Norge",
    "03 - Vest": "Vest",
    "04 - Sør": "Sør",
    "04 - Møre og Romsdal": "Midt-Norge",
    "05 - Øst": "Øst",
    "05 - Vestland": "Vest",
    "06 - Rogaland": "Vest",
    "07 - Agder": "Sør",
    "08 - Vestfold og Telemark": "Sør",
    "09 - Viken": "Øst",
    "09 - Viken - Sørvest": "Sør", # Sørvest is typically Sør region
    "10 - Innlandet": "Øst",
    "11 - Oslo og Viken": "Øst",
    "12 - Bufdir": "Bufdir",
    "06 - Bufdir": "Bufdir",
    
    # Bufdir – eget direktorat (ikke region)
    "Bufdir": "Bufdir",
}

async def fix_regions():
    async with SessionLocal() as db:
        print("Starting Region Fix...")
        for old_val, new_val in MAPPING.items():
            # Update query
            stmt = (
                update(Property)
                .where(Property.region == old_val)
                .values(region=new_val)
            )
            result = await db.execute(stmt)
            if result.rowcount > 0:
                print(f"Updated {result.rowcount} properties from '{old_val}' to '{new_val}'")
            
        await db.commit()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(fix_regions())
