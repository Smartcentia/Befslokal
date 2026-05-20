import sys
import os
import asyncio
import csv
import re
from datetime import datetime

sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Modeller
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party
from app.domains.core.models.property_annual_cost import PropertyAnnualCost

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Mangler DATABASE_URL miljøvariabel.")
    sys.exit(1)

# Ensure asyncpg
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

def parse_float(val: str) -> float:
    if not val:
        return 0.0
    # Clean up non-numeric except digits and comma/dot
    val = str(val).split(",")[0] # If decimals, we can ignore them or use them if we like. But formatting is often e.g. 420000 (Leie fra ...)
    
    # Try to extract the first set of continuous digits
    match = re.search(r'(\d+[\d\s]*\d|\d+)', val)
    if match:
        clean_val = match.group(1).replace(" ", "")
        try:
            return float(clean_val)
        except:
            return 0.0
    return 0.0

def parse_date(val: str):
    if not val:
        return None
    try:
        return datetime.strptime(val.strip(), "%d.%m.%Y").date()
    except:
        return None

async def main():
    csv_file = "/Users/frank/Documents/BEFS_CLEAN/finans/Eiendomsportefølje_ 2025.csv"
    if not os.path.exists(csv_file):
        print(f"File not found: {csv_file}")
        return

    print("Reading data from CSV...")
    data = []
    with open(csv_file, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            if row.get("Lokalisering"):
                data.append(row)

    print(f"Found {len(data)} rows with Lokalisering.")

    async with AsyncSessionLocal() as session:
        for row in data:
            # 1. Hent lokalisering ID f.eks "2330" fra "2330 - Familievern-kontoret i Namsos"
            lok_raw = row.get("Lokalisering", "")
            match = re.match(r"^(\d{4})", lok_raw.strip())
            if not match:
                print(f"Skipping rad med ukjent lokalisering-format: {lok_raw}")
                continue
            lok_id = match.group(1)

            # Finn eiendom
            result = await session.execute(select(Property).where(Property.lokalisering_id == lok_id))
            prop = result.scalars().first()

            if not prop:
                print(f"Advarsel: Fant ikke eiendom i DB med lokalisering_id={lok_id}")
                continue
                
            # Finne/Oppdatere eller opprette part for utleier
            utleier_navn = row.get("Utleier", "").strip()
            utleier_org = row.get("org nr utleier", "").replace(" ", "").strip()
            party = None
            if utleier_navn:
                # Se om vi har parten!
                party_query = select(Party).where(Party.name == utleier_navn)
                party_result = await session.execute(party_query)
                party = party_result.scalars().first()
                if not party:
                    party = Party(name=utleier_navn, organization_number=utleier_org, party_type="Utleier")
                    session.add(party)
                    await session.commit()
                    await session.refresh(party)

            # Finn aktiv kontrakt (eller en generisk placeholder-kontrakt)
            contract_result = await session.execute(select(Contract).where(Contract.status == "Aktiv"))
            # Siden properties ikke lenger er knyttet direkte fra Contract (de går via Unit),
            # og hvis schema endret, slår vi den opp som "aktiv" om vi har parti_id.
            
            # Gitt at kontrakter ligger på Units, må vi finne Unit for denne property. For enkelthets skyld
            # i vår første kjøring, knytter vi ContractAnnualCost mot property_id (og optionally contract_id hvis vi finner).
            
            # 3. Hent inn økonomiske data
            # KPI-justert kontraktsleie til okt 2025
            kpi_adjusted_rent = parse_float(row.get("KPI-justert kontraktsleie til okt 2025", ""))
            internal_maintenance = parse_float(row.get("KPI-justert indre vedlikehold", ""))
            
            # Hvis 'KPI-justert indre vedlikehold' er tomt prøv 'Indre vedlikehold'
            if internal_maintenance == 0.0:
                 internal_maintenance = parse_float(row.get("Indre vedlikehold", ""))
                 
            common_costs = parse_float(row.get("Felleskostnader per år (ved kontraktsinngåelse) ", ""))
            energy_costs = parse_float(row.get("Energi til leieobjektet kr per år", ""))
            heating_costs = parse_float(row.get("Oppvarming pr år", ""))
            cleaning_costs = parse_float(row.get("Renhold pr år", ""))
            parking_rent = parse_float(row.get("Parkeringsleie kr per år", ""))
            caretaker_cost = parse_float(row.get("Vaktmestertjenester kr per år", ""))
            card_reader_cost = parse_float(row.get("Kost kortleser", ""))

            # Sjekk om posten for 2025 allerede finnes
            annual_cost_q = select(PropertyAnnualCost).where(
                PropertyAnnualCost.property_id == prop.property_id,
                PropertyAnnualCost.year == 2025
            )
            ac_res = await session.execute(annual_cost_q)
            annual_cost = ac_res.scalars().first()

            if not annual_cost:
                annual_cost = PropertyAnnualCost(
                    property_id=prop.property_id,
                    year=2025
                )
                session.add(annual_cost)

            annual_cost.kpi_adjusted_rent = kpi_adjusted_rent
            annual_cost.internal_maintenance = internal_maintenance
            annual_cost.common_costs = common_costs
            annual_cost.energy_costs = energy_costs
            annual_cost.heating_costs = heating_costs
            annual_cost.cleaning_costs = cleaning_costs
            annual_cost.parking_rent = parking_rent
            annual_cost.caretaker_cost = caretaker_cost
            annual_cost.card_reader_cost = card_reader_cost
            annual_cost.external_data = row # Store the raw row

            await session.commit()
            print(f"Oppdatert kostnader for {lok_id}: KPI Leie {kpi_adjusted_rent} NOK, Felles {common_costs}")

    print("Import fullført.")

if __name__ == "__main__":
    asyncio.run(main())
