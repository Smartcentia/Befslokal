import asyncio
import csv
import sys
import os
import re
from datetime import datetime
from decimal import Decimal
from sqlalchemy import select, or_

# Add the project root and backend to the python path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from backend.app.db.session import SessionLocal
from backend.app.domains.core.models.property import Property
from backend.app.domains.core.models.contract import Contract
from backend.app.domains.core.models.user import User
from backend.app.domains.hms.models.risk import RiskAssessment
from backend.app.domains.hms.models.internal_control import InternalControlCase
from backend.app.domains.core.models.party import Party
from backend.app.domains.core.models.unit import Unit

# Mapping from CSV Header to Internal Fields.
# Sentral schema: app.domains.core.utils.csv_source_mapping.EIE1212_SCHEMA
MAPPING = {
    # Core Property
    "lokalisering": "address",
    "avtalenavn": "name",
    "areal": "total_area",
    "type lokasjon": "usage", # Map to 'usage' column
    "tomteareal": "land_area",
    "p-plasser": "parking_spots",
    "lok: distrikt": "region", # Map to 'region' column
    
    # Core Contract
    "status": "status",
    "startdato": "start_date", # Fixed typo 'startdata'
    "sluttdato": "end_date",
    
    # Financials (Contract)
    "kpi-justert kontraktsleie til okt 2025": "amount.amount_per_year",
}

def parse_currency(value_str):
    if not value_str:
        return None
    # Remove spaces and normalize decimal comma
    clean_val = value_str.replace(" ", "").replace("\xa0", "").replace(",", ".")
    try:
        return float(clean_val)
    except ValueError:
        return 0.0

def parse_date(date_str):
    if not date_str:
        return None
    try:
        # Expected format: 08.01.2007 (DD.MM.YYYY)
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        return None

def parse_bool_from_text(text):
    if not text:
        return None
    return str(text).lower() in ("ja", "true", "yes", "x")

def extract_postal_data(row):
    # Try to extract city and zip from "adresse og postnummer" or "poststed"
    full_addr = row.get("adresse og postnummer", "")
    city = row.get("poststed", "").title()
    zip_code = None
    
    if full_addr and "," in full_addr:
        parts = [p.strip() for p in full_addr.split(",")]
        for p in parts:
            zip_match = re.search(r'\b(\d{4})\b', p)
            if zip_match:
                zip_code = zip_match.group(1)
                # If city wasn't in field, take it from after zip
                if not city:
                    city_part = p.replace(zip_code, "").strip()
                    if city_part:
                        city = city_part.title()
    
    # Fallback zip search in entire row
    if not zip_code:
        for val in row.values():
            if isinstance(val, str):
                zip_match = re.search(r'\b(\d{4})\b', val)
                if zip_match:
                    zip_code = zip_match.group(1)
                    break
                    
    return zip_code, city


def normalize_region(region_str):
    """Normaliser region til standardformat (Nord, Midt-Norge, Vest, Sør, Øst, Bufdir)."""
    if not region_str:
        return None
    r = region_str.strip().upper()
    mapping = {
        "VEST": "Vest",
        "ØST": "Øst",
        "SØR": "Sør",
        "NORD": "Nord",
        "MIDT": "Midt-Norge",
        "MIDT-NORGE": "Midt-Norge",
        "BUFDIR": "Bufdir",
        "01 - NORD": "Nord",
        "01 - NORDLAND": "Nord",
        "02 - MIDT-NORGE": "Midt-Norge",
        "02 - MIDT": "Midt-Norge",
        "03 - VEST": "Vest",
        "04 - SØR": "Sør",
        "05 - ØST": "Øst",
        "06 - BUFDIR": "Bufdir",
        "12 - BUFDIR": "Bufdir",
    }
    if r in mapping:
        return mapping[r]
    if "REGION" in r:
        if "VEST" in r:
            return "Vest"
        if "ØST" in r:
            return "Øst"
        if "SØR" in r:
            return "Sør"
        if "NORD" in r:
            return "Nord"
        if "MIDT" in r:
            return "Midt-Norge"
    if "01 - " in r and "NORD" in r:
        return "Nord"
    if "02 - " in r and "MIDT" in r:
        return "Midt-Norge"
    if "03 - " in r and "VEST" in r:
        return "Vest"
    if "04 - " in r and "SØR" in r:
        return "Sør"
    if "05 - " in r and "ØST" in r:
        return "Øst"
    if ("06 - " in r or "12 - " in r) and "BUFDIR" in r:
        return "Bufdir"
    return region_str

async def import_master_data():
    csv_file_path = "backend/docs/Eie1212.csv"
    
    log_file = "backend/import_master.log"
    with open(log_file, "a") as f:
        f.write(f"[{datetime.now()}] Script started. Target: {csv_file_path}\n")

    if not os.path.exists(csv_file_path):
        if os.path.exists("docs/Eie1212.csv"):
             csv_file_path = "docs/Eie1212.csv"
        else:
            with open(log_file, "a") as f:
                f.write(f"[{datetime.now()}] Error: File not found at {csv_file_path}\n")
            return
    
    with open(log_file, "a") as f:
        f.write(f"[{datetime.now()}] Using file: {csv_file_path}\n")

    try:
        async with SessionLocal() as session:
            # Pre-fetch all properties to minimize DB hits and enable fuzzy matching if needed
            result = await session.execute(select(Property))
            all_properties = result.scalars().all()
            
            # Simple address lookup map (normalized)
            # We strip spaces and lowercase for matching
            prop_map = {p.address.lower().strip(): p for p in all_properties if p.address}
            
            with open(log_file, "a") as f:
                f.write(f"[{datetime.now()}] Loaded {len(all_properties)} properties from DB. Map size: {len(prop_map)}\n")
                if len(prop_map) > 0:
                    sample_keys = list(prop_map.keys())[:5]
                    f.write(f"[{datetime.now()}] DB Address Samples: {sample_keys}\n")
            
            updated_props = 0
            updated_contracts = 0
            created_contracts = 0
            missed_addresses = []
            
            with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
                # Use DictReader to map by header name
                reader = csv.DictReader(csvfile, delimiter=';') # Semicolon delimiter based on previous file knowledge
                # Normalize headers: strip BOM if present (handled by sig) and whitespace, then lower()
                reader.fieldnames = [name.lower().strip() for name in reader.fieldnames]
                
                for row in reader:
                    # 1. FIND PROPERTY
                    # Caching address-based match (using 'adresselinje 1' as it matches DB 'address')
                    street_address = row.get("adresselinje 1", "").strip()
                    location_full = row.get("lokalisering", "").strip()
                    
                    # Extract name from "ID - Name" format if possible
                    loc_name_clean = location_full
                    if " - " in location_full:
                        parts = location_full.split(" - ", 1)
                        loc_name_clean = parts[1].strip()

                    # Try Matching Strategy:
                    # 1. By exact street address
                    prop = prop_map.get(street_address.lower())
                    
                    # 2. By Name
                    if not prop and loc_name_clean:
                        prop = next((p for p in all_properties if p.name and p.name.lower() == loc_name_clean.lower()), None)
                    
                    # 3. By Full Location String
                    if not prop:
                        prop = next((p for p in all_properties if p.name and p.name.lower() == location_full.lower()), None)
                    
                    if not prop:
                        if len(missed_addresses) < 10:
                            missed_addresses.append(location_full)
                        continue

                    # 2. UPDATE PROPERTY FIELDS
                    # Core fields
                    if row.get("areal"):
                        prop.total_area = parse_currency(row.get("areal"))
                    if row.get("type lokasjon"):
                        prop.usage = row.get("type lokasjon")
                    if row.get("lok: distrikt"):
                        prop.region = row.get("lok: distrikt")
                    if row.get("kommunenavn"):
                        prop.municipality = row.get("kommunenavn")

                    # Geographical Extraction
                    zip_code, city = extract_postal_data(row)
                    if zip_code:
                        prop.postal_code = zip_code
                    if city:
                        prop.city = city
                        
                    # Update region with normalization
                    raw_region = row.get("lok: distrikt")
                    if raw_region:
                         prop.region = normalize_region(raw_region)

                    # External Data - Master Data
                    if not prop.external_data:
                        prop.external_data = {}
                    
                    # Ensure structure exists
                    master_data = prop.external_data.get("master_data", {})
                    financials = prop.external_data.get("financials", {})
                    stats = prop.external_data.get("stats", {})
                    
                    # Master Data Mapping
                    master_data["archive_name"] = row.get("elements")
                    master_data["full_address"] = row.get("adresse og postnummer")
                    master_data["region"] = normalize_region(row.get("lok: distrikt"))
                    master_data["area"] = row.get("lok: område")
                    master_data["target_group"] = row.get("målgruppe")
                    master_data["title_holder"] = row.get("hjemmelshaver")
                    
                    # Stats
                    if row.get("antall godkjente plasser"):
                         try:
                             prop.approved_places = int(row.get("antall godkjente plasser"))
                         except ValueError:
                             pass

                    stats["employees"] = row.get("antall ansatte per kontor/familievernkontor", 0)
                    
                    # Property Financials
                    financials["municipal_fees"] = parse_currency(row.get("kostnander: kommunale gebyrer og renovasjon pr år"))
                    financials["energy_cost"] = parse_currency(row.get("energi til leieobjektet kr per år"))
                    financials["heating_cost"] = parse_currency(row.get("oppvarming pr år"))
                    
                    # Update back into JSONB
                    prop.external_data["master_data"] = master_data
                    prop.external_data["financials"] = financials
                    prop.external_data["stats"] = stats
                    
                    updated_props += 1
                    
                    # 2.5 HANDLE UNIT (Default)
                    # Contract links to Unit, so we must ensure a Unit exists for this Property
                    result = await session.execute(select(Unit).where(Unit.property_id == prop.property_id))
                    units = result.scalars().all()
                    unit = units[0] if units else None

                    if not unit:
                        unit = Unit(
                            property_id=prop.property_id,
                            purpose="MasterImportDefault",
                            area_sqm=(prop.total_area if prop.total_area is not None else 0.0),
                            external_data={}
                        )
                        session.add(unit)
                        await session.flush() # Ensure unit_id is generated

                    # 3. HANDLE CONTRACT
                    result = await session.execute(
                        select(Contract).where(Contract.unit_id == unit.unit_id)
                    )
                    contracts = result.scalars().all()
                    active_contract = next((c for c in contracts if c.status == 'active'), None)
                    
                    if not active_contract:
                        if contracts: 
                             if len(contracts) == 1:
                                 active_contract = contracts[0]
                    
                    is_new_contract = False
                    if not active_contract:
                        is_new_contract = True
                        # Ensure Default Party exists
                        default_party_name = "Ukjent Leietaker (Masterdata)"
                        result = await session.execute(select(Party).where(Party.name == default_party_name))
                        default_party = result.scalars().first()
                        
                        if not default_party:
                            default_party = Party(
                                name=default_party_name,
                                orgnr="000000000"
                            )
                            session.add(default_party)
                            await session.flush()

                        active_contract = Contract(
                            unit_id=unit.unit_id,
                            party_id=default_party.party_id,
                            status="active",
                            periods=[],
                            amount={},
                            external_data={}
                        )
                        session.add(active_contract)
                        created_contracts += 1
                    else:
                        updated_contracts += 1
                    
                    # Update Contract Fields
                    raw_status = row.get("status", "active").lower()
                    status_map = {
                        "aktiv": "active",
                        "utløpt": "expired",
                        "avsluttet": "terminated",
                        "oppsagt": "terminated",
                        "active": "active"
                    }
                    active_contract.status = status_map.get(raw_status, "active")
                    active_contract.start_date = parse_date(row.get("startdato"))
                    
                    # Handle "Ubestemt tid" or "Løpende"
                    extension_terms = str(row.get("forlengelse &vilkår", "")).lower()
                    if "ubestemt" in extension_terms or "løpende" in extension_terms:
                        active_contract.end_date = None
                        active_contract.status = "active"
                    else:
                        active_contract.end_date = parse_date(row.get("sluttdato"))
                    
                    # Financial Data
                    rent_amount = parse_currency(row.get("KPI-justert kontraktsleie til okt 2025"))
                    if rent_amount is not None:
                         # Update the main contract amount
                         # We store it as a simple structure or float depending on model. 
                         # Model likely expects JSON or JSONB for complex amount if it's not a simple column.
                         # Checking model... Contract usually has 'amount' field. If it's JSONB, we set structure.
                          # Create a new dict to ensure change is tracked without flag_modified
                          current_amount = {}
                          if active_contract.amount and isinstance(active_contract.amount, dict):
                              current_amount = active_contract.amount.copy()
                          
                          current_amount['amount_per_year'] = rent_amount
                          active_contract.amount = current_amount

                    # Contract Direct Cost Columns
                    active_contract.caretaker_cost = parse_currency(row.get("Vaktmestertjenester kr per år"))
                    active_contract.cleaning_cost = parse_currency(row.get("Renhold pr år"))
                    active_contract.parking_cost = parse_currency(row.get("Parkeringsleie kr per år"))
                    active_contract.card_reader_cost = parse_currency(row.get("Kost kortleser"))

                    # Contract Extended Data
                    if not active_contract.external_data:
                        active_contract.external_data = {}
                    
                    if "financials" not in active_contract.external_data:
                        active_contract.external_data["financials"] = {}
                    if "area" not in active_contract.external_data:
                        active_contract.external_data["area"] = {}
                    if "master_data" not in active_contract.external_data:
                        active_contract.external_data["master_data"] = {}

                    aud_fin = active_contract.external_data["financials"]
                    aud_fin["initial_rent"] = parse_currency(row.get("Kontraktsleie ved oppstart  (opprinnelig)"))
                    aud_fin["rent_adjustment"] = parse_currency(row.get("kontraktsleie ønkning /reduksjon"))
                    aud_fin["cpi_base_date"] = row.get("Oppstartsdato (KPI-grunnlag) - dato")
                    aud_fin["maintenance_internal"] = parse_currency(row.get("Indre vedlikehold"))
                    aud_fin["common_costs"] = parse_currency(row.get("Felleskostnader per år (akonto)"))
                    aud_fin["deposit"] = parse_currency(row.get("Kontantinnskudd kr"))
                    
                    # Areas
                    aud_area = active_contract.external_data["area"]
                    aud_area["gross_area"] = parse_currency(row.get("Areal inkl fellesareal (bruttoareal BTA) -kvm"))
                    aud_area["exclusive_area"] = parse_currency(row.get("Eksklusivt areal (nettoareal) - kvm"))
                    
                    # Flag as dirty/modified for ORM (needed for JSONB sometimes)
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(prop, "external_data")
                    flag_modified(active_contract, "external_data")
                    # Removed flag_modified for amount as we now re-assign the dict above

            await session.commit()
            
            with open(log_file, "a") as f:
                f.write(f"[{datetime.now()}] Import Complete.\n")
                f.write(f"Properties Updated: {updated_props}\n")
                f.write(f"Contracts Updated: {updated_contracts}\n")
                f.write(f"Contracts Created: {created_contracts}\n")
                if len(missed_addresses) > 0:
                   f.write(f"[{datetime.now()}] MISSED Address Samples (CSV): {missed_addresses}\n")

    except Exception as e:
        import traceback
        with open(log_file, "a") as f:
            f.write(f"[{datetime.now()}] EXCEPTION: {e}\n")
            f.write(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(import_master_data())
