#!/usr/bin/env python3
"""
Import Bufetat rental contracts and enrich property data from CSV files.
"""
import sys
import os
from pathlib import Path
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
import pandas as pd
from fuzzywuzzy import fuzz
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal

# Import all models to ensure SQLAlchemy relationships are registered
import app.domains.core.models.user
import app.domains.core.models.property
import app.domains.core.models.contract
import app.domains.core.models.audit
import app.domains.core.models.unit
import app.domains.core.models.party
import app.domains.core.models.center
import app.domains.hms.models.risk
import app.domains.hms.models.internal_control
import app.models.file_meta

# Now import the specific models we need
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party

# Configuration
CSV_PATH = "/Volumes/KINGSTON/csv/Bufetat_leiedata_renset.csv"
DRY_RUN = False  # Set to True for testing without DB writes

def parse_norwegian_date(date_str: str) -> Optional[datetime]:
    """Parse Norwegian date format DD.MM.YYYY"""
    if pd.isna(date_str) or not date_str:
        return None
    try:
        return datetime.strptime(str(date_str).strip(), "%d.%m.%Y")
    except ValueError:
        try:
            # Try alternative format
            return datetime.strptime(str(date_str).strip(), "%d/%m/%Y")
        except ValueError:
            print(f"⚠️  Could not parse date: {date_str}")
            return None

def parse_amount(amount_str: str) -> Optional[float]:
    """Parse Norwegian number format (spaces as thousand separator)"""
    if pd.isna(amount_str) or not amount_str:
        return None
    try:
        # Remove spaces and convert
        cleaned = str(amount_str).replace(" ", "").replace(",", ".")
        return float(cleaned)
    except ValueError:
        print(f"⚠️  Could not parse amount: {amount_str}")
        return None

def normalize_address(addr: str) -> str:
    """Normalize address for matching"""
    if not addr:
        return ""
    return addr.lower().strip().replace("  ", " ")

def find_best_property_match(csv_address: str, properties: List[Property]) -> Optional[Property]:
    """Find best matching property using fuzzy matching"""
    if not csv_address:
        return None
    
    csv_norm = normalize_address(csv_address)
    best_match = None
    best_score = 0
    
    for prop in properties:
        if not prop.address:
            continue
        
        prop_norm = normalize_address(prop.address)
        score = fuzz.ratio(csv_norm, prop_norm)
        
        if score > best_score:
            best_score = score
            best_match = prop
    
    # Require at least 80% match
    if best_score >= 80:
        return best_match
    
    return None

async def load_csv_data(filepath: str) -> pd.DataFrame:
    """Load CSV with proper encoding"""
    print(f"📂 Loading CSV: {filepath}")
    
    # Try UTF-8 with BOM first
    try:
        df = pd.read_csv(filepath, sep=";", encoding="utf-8-sig")
        print(f"✅ Loaded {len(df)} rows")
        return df
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        raise

async def enrich_properties(db: AsyncSession, csv_data: pd.DataFrame):
    """Enrich existing properties with metadata from CSV"""
    print("\n🔧 Phase 1: Enriching Properties")
    
    # Load all properties
    result = await db.execute(select(Property))
    properties = list(result.scalars().all())
    print(f"Found {len(properties)} existing properties")
    
    enriched_count = 0
    
    for idx, row in csv_data.iterrows():
        csv_address = row.get("Adresselinje 1", "")
        
        # Find matching property
        prop = find_best_property_match(csv_address, properties)
        
        if not prop:
            print(f"⚠️  No match for: {csv_address}")
            continue
        
        # Update fields
        updates = {}
        
        if pd.notna(row.get("Lok: Område")):
            updates["region"] = row["Lok: Område"]
        
        if pd.notna(row.get("kommunenavn")):
            updates["municipality"] = row["kommunenavn"]
        
        if pd.notna(row.get("org nr utleier")):
            updates["org_number"] = str(row["org nr utleier"])
        
        if pd.notna(row.get("Matrikkel Gnr")):
            try:
                updates["gnr"] = int(row["Matrikkel Gnr"])
            except:
                pass
        
        if pd.notna(row.get("Matrikkel Bnr")):
            bnr_str = str(row["Matrikkel Bnr"])
            # Handle "783 og 411 (snr1 og 2)" format
            if " og " in bnr_str:
                bnr_str = bnr_str.split(" og ")[0]
            try:
                updates["bnr"] = int(bnr_str.split()[0])
            except:
                pass
        
        if pd.notna(row.get("Areal inkl fellesareal i leiekontrakt (kvm)")):
            updates["total_area"] = parse_amount(row["Areal inkl fellesareal i leiekontrakt (kvm)"])
        
        if pd.notna(row.get("Antall godkjente plasser")):
            try:
                updates["approved_places"] = int(row["Antall godkjente plasser"])
            except:
                pass
        
        if updates:
            for key, value in updates.items():
                setattr(prop, key, value)
            enriched_count += 1
    
    if not DRY_RUN:
        await db.commit()
    
    print(f"✅ Enriched {enriched_count} properties")

async def import_parties(db: AsyncSession, csv_data: pd.DataFrame) -> Dict[str, uuid.UUID]:
    """Import landlords as parties, return mapping org_number -> party_id"""
    print("\n👥 Phase 2: Importing Parties (Landlords)")
    
    parties_map = {}
    unique_landlords = csv_data[["Utleier", "org nr utleier"]].drop_duplicates()
    
    for idx, row in unique_landlords.iterrows():
        landlord_name = row.get("Utleier")
        org_number = row.get("org nr utleier")
        
        if pd.isna(landlord_name):
            continue
        
        # Parse org number safely
        org_num_str = None
        if pd.notna(org_number) and org_number != '':
            try:
                org_num_str = str(int(org_number))
            except (ValueError, TypeError):
                # Handle "privat" or other non-numeric values
                pass
        
        # Check if party already exists (by org number OR name)
        existing = None
        if org_num_str:
            result = await db.execute(
                select(Party).where(Party.orgnr == org_num_str)
            )
            existing = result.scalar_one_or_none()
        
        if not existing:
            # Also check by name to avoid duplicates
            result = await db.execute(
                select(Party).where(Party.name == landlord_name)
            )
            existing = result.scalar_one_or_none()
        
        if existing:
            if org_num_str:
                parties_map[org_num_str] = existing.party_id
            continue
        
        # Create new party
        party = Party(
            party_id=uuid.uuid4(),
            name=landlord_name,
            orgnr=org_num_str,
            external_data={"party_type": "landlord"}
        )
        
        db.add(party)
        
        # Store ID before commit
        party_id_to_store = party.party_id
        
        # Commit immediately to avoid batch conflicts
        if not DRY_RUN:
            try:
                await db.commit()
            except Exception as e:
                print(f"  ⚠️  Failed to add {landlord_name}: {e}")
                await db.rollback()
                continue
        
        if org_num_str:
            parties_map[org_num_str] = party_id_to_store
        
        print(f"  + {landlord_name} ({org_num_str})")
    
    print(f"✅ Imported {len(parties_map)} parties")
    return parties_map

async def import_contracts(db: AsyncSession, csv_data: pd.DataFrame, parties_map: Dict[str, uuid.UUID]):
    """Import rental contracts"""
    print("\n📄 Phase 3: Importing Contracts")
    
    # Load properties and units
    result = await db.execute(select(Property))
    properties = list(result.scalars().all())
    
    result = await db.execute(select(Unit))
    units = list(result.scalars().all())
    
    # Create property_id -> unit_id mapping
    unit_map = {unit.property_id: unit.unit_id for unit in units}
    
    imported_count = 0
    skipped_count = 0
    
    for idx, row in csv_data.iterrows():
        csv_address = row.get("Adresselinje 1", "")
        
        # Find matching property
        prop = find_best_property_match(csv_address, properties)
        
        if not prop:
            print(f"⚠️  Skipping contract (no property match): {csv_address}")
            skipped_count += 1
            continue
        
        # Get unit for this property
        unit_id = unit_map.get(prop.property_id)
        
        if not unit_id:
            print(f"⚠️  Skipping contract (no unit): {prop.address}")
            skipped_count += 1
            continue
        
        # Get party
        org_num = str(row.get("org nr utleier")) if pd.notna(row.get("org nr utleier")) else None
        party_id = parties_map.get(org_num) if org_num else None
        
        # Parse dates
        start_date = parse_norwegian_date(row.get("Startdato"))
        end_date = parse_norwegian_date(row.get("Sluttdato"))
        
        # Parse amounts
        annual_rent = parse_amount(row.get("Kontraktsleie ved oppstart (per år)"))
        
        # Map status
        status_str = row.get("Status", "").lower()
        status = "active" if "aktiv" in status_str else "terminated"
        
        # Build amount object
        amount = {
            "amount_per_year": annual_rent,
            "currency": "NOK"
        }
        
        # Build external_data (replace NaN with None for JSON compatibility)
        external_data = {
            "contract_name": row.get("Avtalenavn") if pd.notna(row.get("Avtalenavn")) else None,
            "regulation_type": row.get("leieregulering") if pd.notna(row.get("leieregulering")) else None,
            "extension_terms": row.get("Forlengelse og vilkår") if pd.notna(row.get("Forlengelse og vilkår")) else None,
            "parking_spaces": row.get("p-plasser") if pd.notna(row.get("p-plasser")) else None,
            "common_costs": parse_amount(row.get("Felleskostnader per år (ved kontraktsinngåelse)")),
            "user_dependent_costs": parse_amount(row.get("Brukeravhengige driftskostander - Første driftsår")),
            "internal_maintenance_cost": parse_amount(row.get("Kostnad til indre vedlikehold per år")),
            "municipal_fees": parse_amount(row.get("Kostnander: kommunale gebyrer og renovasjon")),
            "energy_cost": parse_amount(row.get("Energi til leieobjektet kr per år")),
            "heating_cost": parse_amount(row.get("Oppvarming pr år")),
            "deposit": parse_amount(row.get("Kontantinnskudd kr")),
        }
        
        # Create contract
        contract = Contract(
            contract_id=uuid.uuid4(),
            unit_id=unit_id,
            party_id=party_id,
            status=status,
            category="Leiekontrakt",
            start_date=start_date,
            end_date=end_date,
            amount=amount,
            caretaker_cost=parse_amount(row.get("Vaktmestertjenester kr per år")),
            cleaning_cost=parse_amount(row.get("Renhold pr år")),
            parking_cost=parse_amount(row.get("Parkeringsleie kr per år")),
            card_reader_cost=parse_amount(row.get("Kost kortleser")),
            external_data=external_data
        )
        
        db.add(contract)
        imported_count += 1
        
        if imported_count % 50 == 0:
            print(f"  Imported {imported_count} contracts...")
    
    if not DRY_RUN:
        await db.commit()
    
    print(f"✅ Imported {imported_count} contracts")
    print(f"⚠️  Skipped {skipped_count} contracts (no match)")

async def validate_import(db: AsyncSession):
    """Validate the import results"""
    print("\n✅ Validation")
    
    # Count contracts
    result = await db.execute(select(Contract))
    contracts = result.scalars().all()
    print(f"  Total contracts: {len(list(contracts))}")
    
    # Count parties
    result = await db.execute(select(Party))
    parties = result.scalars().all()
    print(f"  Total parties: {len(list(parties))}")
    
    # Count enriched properties
    result = await db.execute(select(Property).where(Property.region.isnot(None)))
    enriched = result.scalars().all()
    print(f"  Properties with region: {len(list(enriched))}")

async def main():
    """Main import workflow"""
    print("🚀 Bufetat Contract Import")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE IMPORT'}")
    print("=" * 60)
    
    # Load CSV
    csv_data = await load_csv_data(CSV_PATH)
    
    # Connect to database
    async with SessionLocal() as db:
        # Phase 1: Enrich properties
        await enrich_properties(db, csv_data)
        
        # Phase 2: Import parties
        parties_map = await import_parties(db, csv_data)
        
        # Phase 3: Import contracts
        await import_contracts(db, csv_data, parties_map)
        
        # Validate
        await validate_import(db)
    
    print("\n✅ Import complete!")

if __name__ == "__main__":
    asyncio.run(main())
