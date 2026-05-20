import asyncio
from app.db.session import SessionLocal
from sqlalchemy import text
import sys

async def check_jernbaneveien():
    async with SessionLocal() as db:
        # Check property
        res = await db.execute(text("SELECT property_id, address, total_area, construction_year FROM properties WHERE address LIKE '%Jernbaneveien 70%'"))
        prop = res.fetchone()
        if not prop:
            print("Property not found")
            return
        
        print(f"Property: {prop.address} (ID: {prop.property_id})")
        print(f"Area: {prop.total_area}, Year: {prop.construction_year}")
        
        # Check units
        res = await db.execute(text("SELECT unit_id, purpose, area_sqm FROM units WHERE property_id = :pid"), {"pid": prop.property_id})
        units = res.all()
        print(f"\nUnits ({len(units)}):")
        for u in units:
            print(f"- {u.purpose}: {u.area_sqm} m2 (ID: {u.unit_id})")
            
            # Check contracts for this unit
            res = await db.execute(text("SELECT contract_id, party_id, status FROM contracts WHERE unit_id = :uid"), {"uid": u.unit_id})
            contracts = res.all()
            for c in contracts:
                print(f"  -> Contract: {c.contract_id}, Party: {c.party_id}, Status: {c.status}")
                
                # Check party
                res = await db.execute(text("SELECT name FROM parties WHERE party_id = :paid"), {"paid": c.party_id})
                party = res.fetchone()
                if party:
                    print(f"     -> Party Name: {party.name}")

if __name__ == "__main__":
    asyncio.run(check_jernbaneveien())
