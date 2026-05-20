
import asyncio
import sys
import os
import json
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
# Related models
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.user import User
from app.domains.core.models.party import Party

RECHARGED_HUBS = [
    "Portalen", "Veni Metering", "Lillestrøm",
    "Kvartal 71", "Grønland 68", "Bufetathus Drammen", "Bufetathus Kristiansand",
    "Pirsenteret", "GC Rieber", "Solheimsviken",
    "Statens Hus", "Statsforvalteren i Rogaland"
]

DIRECT_PROVIDERS = ["Kinect Energy Spot AS", "Ishavskraft AS", "Elvia", "Lnett", "BKK", "Tensio", "Arva"]

async def enrich_energy():
    async with SessionLocal() as db:
        res = await db.execute(select(Property))
        props = res.scalars().all()
        
        tagged_recharged = 0
        tagged_direct = 0
        
        for p in props:
            fin = p.external_data.get('financials', {})
            expenses = fin.get('manual_expenses', [])
            
            profile = "Unknown"
            logic = ""
            
            # Check for Recharged Hubs in name/address/providers
            is_hub = False
            for hub in RECHARGED_HUBS:
                if (p.name and hub.lower() in p.name.lower()) or (p.address and hub.lower() in p.address.lower()):
                    is_hub = True
                    logic = f"Matched hub keyword: {hub}"
                    break
            
            if not is_hub:
                for e in expenses:
                    provider = e.get('provider', '')
                    for hub in RECHARGED_HUBS:
                        if hub.lower() in provider.lower():
                            is_hub = True
                            logic = f"Matched hub provider: {provider}"
                            break
                    if is_hub: break
            
            if is_hub:
                profile = "Recharged via Landlord"
                tagged_recharged += 1
            else:
                # Check for Direct Providers
                is_direct = False
                for e in expenses:
                    provider = e.get('provider', '')
                    for dp in DIRECT_PROVIDERS:
                        if dp.lower() in provider.lower():
                            is_direct = True
                            logic = f"Matched direct provider: {provider}"
                            break
                    if is_direct: break
                
                if is_direct:
                    profile = "Direct Meter"
                    tagged_direct += 1
            
            if profile != "Unknown":
                energy_data = {
                    "profile": profile,
                    "logic": logic,
                    "manual_verification_required": False
                }
                fin['energy_profile'] = energy_data
                p.external_data['financials'] = fin
                flag_modified(p, "external_data")
                db.add(p)
        
        await db.commit()
        print(f"Energy Profiling Summary:")
        print(f"- Properties tagged as 'Recharged via Landlord': {tagged_recharged}")
        print(f"- Properties tagged as 'Direct Meter': {tagged_direct}")

if __name__ == "__main__":
    asyncio.run(enrich_energy())
