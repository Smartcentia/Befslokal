
import csv
import asyncio
from sqlalchemy.future import select
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control
import app.domains.core.models.user
import re

async def fix_names():
    csv_path = "/Users/frank/BEFS3/KNOWME/backend/docs/Eiendomsportefølje_ 2025.csv"
    
    async with SessionLocal() as db:
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                rows = list(reader)
                
                updates = 0
                for row in rows:
                    location_id_raw = row.get("Lokalisering", "")
                    if not location_id_raw:
                        continue
                    
                    parts = location_id_raw.split(" - ", 1)
                    loc_id = parts[0].strip()
                    
                    # Search by legacy ID in external_data
                    # external_data looks like {"legacy_id": "5103"}
                    stmt = select(Property).where(Property.external_data["legacy_id"].astext == loc_id)
                    result = await db.execute(stmt)
                    property_obj = result.scalars().first()
                    
                    if not property_obj:
                        # Fallback to address matching if legacy ID lookup fails
                        addr = row.get("Adresselinje 1", "")
                        if addr:
                            stmt = select(Property).where(Property.address == addr)
                            result = await db.execute(stmt)
                            property_obj = result.scalars().first()

                    if property_obj:
                        # Determine a better name
                        avtale_navn = row.get("Avtalenavn", "").strip()
                        type_lokasjon = row.get("Type lokasjon", "").strip()
                        poststed = row.get("Poststed", "").strip()
                        
                        current_name = property_obj.name
                        new_name = None
                        
                        # logic: If Avtalenavn is descriptive, use it.
                        # Descriptive means it doesn't look like just an address or ID.
                        if avtale_navn and not re.search(r'^\d{4}', avtale_navn):
                            new_name = avtale_navn
                        elif type_lokasjon and poststed:
                            new_name = f"{type_lokasjon} {poststed.title()}"
                        elif type_lokasjon:
                            new_name = type_lokasjon
                            
                        if new_name and new_name != current_name:
                            print(f"Updating '{current_name}' -> '{new_name}' (ID: {loc_id})")
                            property_obj.name = new_name
                            updates += 1
                
                if updates > 0:
                    await db.commit()
                    print(f"Successfully updated {updates} properties.")
                else:
                    print("No properties needed updating.")
                    
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(fix_names())
