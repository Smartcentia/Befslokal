
import asyncio
import sys
import os
from sqlalchemy import select
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property

SHADOW_PORTFOLIO = ["Barkåker", "Mynten", "Kvammen", "Silsand", "Toppe"]
CONTRACTS_2099 = [
    "Ramsrudveien 32", "Bjørlistubben 14", "Ullsvei 16", "Alfheimvn 6", 
    "Skolegata 53", "Wiulls gate 3", "Lundebyveien 363", "Veslekila 1", 
    "Kantarellveien 4"
]

async def check_database():
    async with SessionLocal() as db:
        print("--- Checking Shadow Portfolio (Missing in Kontrakt ID.txt) ---")
        for name in SHADOW_PORTFOLIO:
            # Fuzzy like search
            stmt = select(Property).where(Property.name.ilike(f"%{name}%"))
            result = await db.execute(stmt)
            prop = result.scalars().first()
            if prop:
                print(f"[FOUND] {name}: ID={prop.id}, Name='{prop.name}'")
            else:
                print(f"[MISSING] {name}")

        print("\n--- Checking 2099 Contracts ---")
        for name in CONTRACTS_2099:
            stmt = select(Property).where(Property.name.ilike(f"%{name}%"))
            result = await db.execute(stmt)
            prop = result.scalars().first()
            
            if prop:
                lease_end = "N/A"
                if prop.external_data and 'contract' in prop.external_data:
                     lease_end = prop.external_data['contract'].get('lease_end', 'N/A')
                
                print(f"[FOUND] {name}: Lease End='{lease_end}'")
            else:
                print(f"[MISSING] {name}")

        # Check for div3 specific knowledge
        print("\n--- Checking for div3 specific data (Risk Analysis) ---")
        stmt = select(Property).where(Property.external_data.isnot(None))
        result = await db.execute(stmt)
        props = result.scalars().all()
        
        found_analysis = False
        for p in props:
            if not p.external_data: continue
            
            # Check for 'analysis' or specific div3 keys
            if 'risk_analysis' in p.external_data or 'div3_source' in str(p.external_data):
                print(f"[FOUND] Analysis data found on {p.name}")
                found_analysis = True
                break
        
        if not found_analysis:
            print("[MISSING] No specific 'div3' risk analysis data found in external_data.")

if __name__ == "__main__":
    asyncio.run(check_database())
