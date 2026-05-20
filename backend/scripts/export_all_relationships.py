import asyncio
import json
import os
import ssl
from uuid import UUID
from datetime import date, datetime
from dotenv import load_dotenv

# Load environment variables before importing app components
env_path = os.path.join(os.getcwd(), '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(os.path.dirname(os.getcwd()), '.env')
    
print(f"DEBUG: Forsøker å laste .env fra {env_path}")
load_dotenv(dotenv_path=env_path)

db_url_env = os.environ.get("DATABASE_URL")
if db_url_env:
    print(f"DEBUG: DATABASE_URL funnet i os.environ: {db_url_env[:20]}...")
else:
    print("DEBUG: DATABASE_URL IKKE funnet i os.environ!")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import selectinload, sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

async def main():
    database_url = settings.DATABASE_URL
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    _ssl = ssl_context
    if database_url and ".railway.internal" in database_url:
        _ssl = False

    engine = create_async_engine(
        database_url,
        echo=False,
        connect_args={"ssl": _ssl}
    )
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with SessionLocal() as session:
        # Load all properties that are NOT departments (parent_unit_id_erp is null or unit_short_type is not Avdeling)
        stmt = select(Property).where(
            (Property.parent_unit_id_erp == None) | (Property.unit_short_type != 'Avdeling')
        )
        result = await session.execute(stmt)
        main_properties = result.scalars().all()
        
        # Load all departments (which point to main properties via parent_unit_id_erp)
        stmt_deps = select(Property).where(Property.parent_unit_id_erp != None, Property.unit_short_type == 'Avdeling')
        result_deps = await session.execute(stmt_deps)
        all_departments = result_deps.scalars().all()
        
        # Load all units with contracts and parties
        stmt_units = select(Unit).options(
            selectinload(Unit.contracts).selectinload(Contract.party)
        )
        # Note: 'units.contracts' isn't explicitly defined as relationship on Unit, 
        # so let's just query contracts and join them manually.
        pass

    # Alternative approach: just query EVERYTHING and piece it together in memory
    async with SessionLocal() as session:
        result = await session.execute(select(Property))
        all_props = result.scalars().all()
        
        result = await session.execute(select(Unit))
        all_units = result.scalars().all()
        
        result = await session.execute(select(Contract).options(selectinload(Contract.party)))
        all_contracts = result.scalars().all()
        
    # Group contracts by unit
    contracts_by_unit = {}
    for c in all_contracts:
        if c.unit_id not in contracts_by_unit:
            contracts_by_unit[c.unit_id] = []
        c_dict = {
            "contract_id": str(c.contract_id),
            "status": c.status,
            "category": c.category,
            "start_date": c.start_date.isoformat() if c.start_date else None,
            "end_date": c.end_date.isoformat() if c.end_date else None,
            "party": {
                "party_id": str(c.party.party_id) if c.party else None,
                "navn": c.party.name if c.party else None,
                "orgnr": c.party.orgnr if c.party else None
            } if c.party else None
        }
        contracts_by_unit[c.unit_id].append(c_dict)
        
    # Group units by property
    units_by_property = {}
    for u in all_units:
        if u.property_id not in units_by_property:
            units_by_property[u.property_id] = []
        u_dict = {
            "unit_id": str(u.unit_id),
            "adresse_eller_beskrivelse": u.address,
            "formal": u.purpose,
            "areal_kvm": u.area_sqm,
            "kontrakter": contracts_by_unit.get(u.unit_id, [])
        }
        units_by_property[u.property_id].append(u_dict)
        
    # Build property hierarchy
    # 1. Map all properties
    prop_map = {}
    for p in all_props:
        prop_map[p.property_id] = {
            "property_id": str(p.property_id),
            "navn": p.name or p.address,
            "lokalisering_id": p.lokalisering_id,
            "adresse": p.address,
            "kommune": p.municipality,
            "unit_short_type": p.unit_short_type,
            "unit_id_erp": p.unit_id_erp,
            "parent_unit_id_erp": p.parent_unit_id_erp,
            "enheter": units_by_property.get(p.property_id, []),
            "avdelinger": []
        }
        
    # 2. Assign departments to their parents
    # We use unit_id_erp -> property mappings to find the parent
    erp_to_prop_id = {p.unit_id_erp: p.property_id for p in all_props if p.unit_id_erp}
    
    main_outputs = []
    
    for p in all_props:
        p_dict = prop_map[p.property_id]
        if p.parent_unit_id_erp and p.parent_unit_id_erp in erp_to_prop_id:
            parent_id = erp_to_prop_id[p.parent_unit_id_erp]
            prop_map[parent_id]["avdelinger"].append(p_dict)
        else:
            # It's a root property
            main_outputs.append(p_dict)
            
    output_data = {
        "metadata": {
            "beskrivelse": "Dette er en komplett eksport av alle eiendommer, avdelinger, enheter, kontrakter og leietakere (parties) fra den faktiske databasen."
        },
        "eiendommer": main_outputs
    }
    
    with open("docs/database_eksport_relasjoner.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"Lagret oppdatert JSON med selve databasenavigasjonen og {len(main_outputs)} hovedeiendommer!")

if __name__ == "__main__":
    asyncio.run(main())
