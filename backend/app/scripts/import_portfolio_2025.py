
import csv
import uuid
import datetime
import asyncio
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
# Import all models to ensure relationships are resolved
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control
import app.domains.core.models.user

def parse_norwegian_float(value_str):
    if not value_str or value_str.strip() == "":
        return None
    try:
        # Remove spaces and replace comma with dot
        clean_str = value_str.replace(" ", "").replace(",", ".")
        return float(clean_str)
    except ValueError:
        return None

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        return None

import re

# Helper to find zip code
def extract_zip_code(address_str):
    if not address_str:
        return None
    match = re.search(r'\b\d{4}\b', address_str)
    return match.group(0) if match else None

async def import_portfolio(csv_path: str):
    async with SessionLocal() as db:
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                rows = list(reader) 
                
                for row in rows:
                    # 1. Identify Property (Lokalisering)
                    location_id_raw = row.get("Lokalisering", "")
                    if not location_id_raw:
                        continue
                    
                    parts = location_id_raw.split(" - ", 1)
                    loc_id = parts[0].strip() if len(parts) > 0 else None
                    loc_name = parts[1].strip() if len(parts) > 1 else location_id_raw

                    # Extract Postal Code
                    full_address = row.get("Adresse og Postnummer", "")
                    zip_code = extract_zip_code(full_address)
                    city = row.get("Poststed", "").title() # Use Poststed as city, capitalize properly

                    # Match Property
                    stmt = select(Property).where(Property.name == loc_name)
                    result = await db.execute(stmt)
                    property_obj = result.scalars().first()

                    if not property_obj:
                        # Fallback: Search by address
                        addr = row.get("Adresselinje 1", "")
                        if addr:
                            stmt = select(Property).where(Property.address == addr)
                            result = await db.execute(stmt)
                            property_obj = result.scalars().first()
                    
                    if not property_obj:
                        print(f"Creating new property: {loc_name}")
                        property_obj = Property(
                            property_id=uuid.uuid4(),
                            name=loc_name,
                            address=row.get("Adresselinje 1"),
                            postal_code=zip_code,
                            city=city,
                            municipality=row.get("kommunenavn"),
                            gnr=int(row.get("Matrikkel Gnr")) if row.get("Matrikkel Gnr") and row.get("Matrikkel Gnr").isdigit() else None,
                            bnr=int(row.get("Matrikkel Bnr")) if row.get("Matrikkel Bnr") and row.get("Matrikkel Bnr").isdigit() else None,
                            total_area=parse_norwegian_float(row.get("Areal")),
                            usage=row.get("Type lokasjon"),
                            external_data={"legacy_id": loc_id}
                        )
                        db.add(property_obj)
                        await db.flush()
                    else:
                        print(f"Updating property: {loc_name}")
                        if row.get("Adresselinje 1"): property_obj.address = row.get("Adresselinje 1")
                        if row.get("kommunenavn"): property_obj.municipality = row.get("kommunenavn")
                        if zip_code: property_obj.postal_code = zip_code
                        if city: property_obj.city = city
                        if row.get("Matrikkel Gnr") and row.get("Matrikkel Gnr").isdigit(): property_obj.gnr = int(row.get("Matrikkel Gnr"))
                        if row.get("Matrikkel Bnr") and row.get("Matrikkel Bnr").isdigit(): property_obj.bnr = int(row.get("Matrikkel Bnr"))
                        area = parse_norwegian_float(row.get("Areal"))
                        if area: property_obj.total_area = area
                        property_obj.usage = row.get("Type lokasjon")
                        # Preserving existing external data
                        if not property_obj.external_data: property_obj.external_data = {}
                        property_obj.external_data.update({"legacy_id": loc_id})

                    # Update new specific column
                    approved_places = row.get("Antall godkjente plasser")
                    if approved_places and approved_places.isdigit():
                        property_obj.approved_places = int(approved_places)

                    # Ensure Unit
                    stmt = select(Unit).where(Unit.property_id == property_obj.property_id)
                    result = await db.execute(stmt)
                    unit = result.scalars().first()

                    if not unit:
                        unit = Unit(
                            unit_id=uuid.uuid4(),
                            property_id=property_obj.property_id,
                            external_data={"generated": True}
                        )
                        db.add(unit)
                        await db.flush()

                    # 2. Contract
                    stmt = select(Contract).where(Contract.unit_id == unit.unit_id)
                    result = await db.execute(stmt)
                    contract = result.scalars().first()
                    
                    if not contract:
                        contract = Contract(
                            contract_id=uuid.uuid4(),
                            unit_id=unit.unit_id,
                            status="active",
                            amount={}, # Default to empty dict to satisfy DB constraint
                            external_data={}
                        )
                        db.add(contract)
                    
                    # Update Contract Fields
                    start_date_val = row.get("Startdato")
                    signed_at_val = parse_date(start_date_val)
                    if signed_at_val:
                        contract.signed_at = signed_at_val
                    
                    end_date_val = row.get("Sluttdato")
                    
                    if start_date_val or end_date_val:
                        contract.periods = {
                            "current": {"start": start_date_val, "end": end_date_val}
                        }

                    # Party
                    landlord_name = row.get("Utleier")
                    if landlord_name:
                        stmt = select(Party).where(Party.name == landlord_name)
                        result = await db.execute(stmt)
                        party = result.scalars().first()
                        
                        if not party:
                            party = Party(party_id=uuid.uuid4(), name=landlord_name, role="landlord")
                            db.add(party)
                            await db.flush()
                        contract.party_id = party.party_id

                    # Financials
                    contract.caretaker_cost = parse_norwegian_float(row.get("Vaktmestertjenester kr per år"))
                    contract.cleaning_cost = parse_norwegian_float(row.get("Renhold pr år"))
                    contract.parking_cost = parse_norwegian_float(row.get("Parkeringsleie kr per år"))
                    contract.card_reader_cost = parse_norwegian_float(row.get("Kost kortleser"))
                    
                    rent = parse_norwegian_float(row.get("Kontraktsleie ved oppstart (per år)"))
                    if rent:
                        if not contract.amount: contract.amount = {}
                        current_amount = dict(contract.amount) if contract.amount else {}
                        current_amount["base_rent"] = rent
                        contract.amount = current_amount # Reassign to trigger update if JSON is mutable warning

                    # Update Info / Notes
                    # We update external_data with notes and extension terms if present
                    if not contract.external_data: contract.external_data = {}
                    current_ext = dict(contract.external_data)
                    
                    comment = row.get("kommentar")
                    if comment and comment.strip():
                        current_ext["kommentar"] = comment.strip()
                    
                    extension_terms = row.get("forlengelse &vilkår")
                    if extension_terms and extension_terms.strip():
                        current_ext["forlengelse_vilkår"] = extension_terms.strip()

                    contract.external_data = current_ext

                await db.commit()
                print("Import completed successfully.")

        except Exception as e:
            print(f"Error during import: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(import_portfolio("/Users/frank/BEFS3/KNOWME/docs/Eiendomsportefølje_ 2025.csv"))
