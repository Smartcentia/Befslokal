import sys
import os
import asyncio
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from dotenv import load_dotenv
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
# Needed for SQLAlchemy mapper initialization to resolve string references in relationships
from app.domains.core.models.center import Center
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.models.file_meta import FileMeta
from app.domains.core.models.user import User
from app.domains.core.models.audit import AuditLog

OUTPUT_FILE = "rapporttotalfeb2026.csv"

async def generate_report():
    print("Starting generation of rapporttotalfeb2026.csv...")
    
    rows = []
    
    async with SessionLocal() as db:
        # Fetch everything
        props_res = await db.execute(select(Property))
        properties = props_res.scalars().all()
        
        units_res = await db.execute(select(Unit))
        units = units_res.scalars().all()
        
        contracts_res = await db.execute(select(Contract).options(selectinload(Contract.party)))
        contracts = contracts_res.scalars().all()
        
        print(f"Found {len(properties)} properties, {len(units)} units, {len(contracts)} contracts.")
        
        # Build lookup maps
        prop_map = {p.property_id: p for p in properties}
        
        # Map units to properties
        units_by_prop = {}
        for u in units:
            pid = u.property_id
            if pid not in units_by_prop: units_by_prop[pid] = []
            units_by_prop[pid].append(u)
            
        # Map contracts to units
        contracts_by_unit = {}
        for c in contracts:
            uid = c.unit_id
            if uid not in contracts_by_unit: contracts_by_unit[uid] = []
            contracts_by_unit[uid].append(c)
            
        for p in properties:
            base_data = {
                "Eiendom_Navn": p.name or "Navnløs",
                "Adresse": p.address,
                "Postnummer": p.postal_code,
                "Poststed": p.city,
                "Region": p.region,
                "Kommune": p.municipality,
                "GNR_BNR": f"{p.gnr or ''}/{p.bnr or ''}",
                "Areal_Totalt": p.total_area,
                "Byggeaar": p.construction_year,
                "Bruk": p.usage,
                "EnhetID_ERP": p.unit_id_erp,
                "Tilhørighet": p.affiliation,
                "Budsjetterte_Plasser": p.budgeted_places,
                "Eierskapstype": p.ownership_type,
                "Nedlagt_Dato": p.closed_at.strftime('%Y-%m-%d') if p.closed_at else "",
                "Lokasjonskode": p.lokalisering_id,
                "Hjemmel": p.legal_basis,
                "Match_Metode": p.external_data.get('last_match_method') if p.external_data else "Ingen match",
                "Match_Score": p.external_data.get('last_match_score') if p.external_data else 0
            }
            
            p_units = units_by_prop.get(p.property_id, [])
            if not p_units:
                rows.append({**base_data, "Enhet_Formaal": "Ingen enheter", "Leietaker": "", "Kontrakt_Status": "", "Belop": ""})
                continue
                
            for unit in p_units:
                unit_data = {
                    "Enhet_Formaal": unit.purpose,
                    "Enhet_Areal": unit.area_sqm,
                    "Etasje": unit.floor
                }
                
                u_contracts = contracts_by_unit.get(unit.unit_id, [])
                if not u_contracts:
                    rows.append({**base_data, **unit_data, "Leietaker": "", "Kontrakt_Status": "", "Belop": ""})
                    continue
                    
                for contract in u_contracts:
                    contract_data = {
                        "Leietaker": contract.party.name if contract.party else "Ukjent",
                        "Kontrakt_Status": contract.status,
                        "Belop": contract.amount,
                        "Signert_Dato": contract.signed_at.strftime('%Y-%m-%d') if contract.signed_at else "",
                        "Opphørsdato": contract.terminated_at.strftime('%Y-%m-%d') if contract.terminated_at else ""
                    }
                    rows.append({**base_data, **unit_data, **contract_data})
                    
    # Create DataFrame and export
    df = pd.DataFrame(rows)
    
    # Force ID columns to string to avoid Pandas '.0' artifact for float conversion
    for col in ['EnhetID_ERP', 'Lokasjonskode']:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).replace(r'\.0$', '', regex=True)

    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig', sep=';')
    
    # Coverage Statistics
    total_rows = len(df)
    filled_erp = df['EnhetID_ERP'].replace('', pd.NA).dropna().count()
    print(f"Coverage Summary:")
    print(f"  - Total rows: {total_rows}")
    print(f"  - EnhetID_ERP filled: {filled_erp}")
    print(f"  - EnhetID_ERP missing: {total_rows - filled_erp}")
    if 'Match_Metode' in df.columns:
        print(f"Matching Stats:")
        print(df['Match_Metode'].value_counts())
    
    print(f"Successfully generated {OUTPUT_FILE} with {len(rows)} rows.")

if __name__ == "__main__":
    asyncio.run(generate_report())
