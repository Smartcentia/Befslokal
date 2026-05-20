import asyncio
import uuid
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import app.db.base # Register models
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from sqlalchemy import select

async def populate_metadata():
    print("Populating property metadata...")
    async with SessionLocal() as db:
        # 1. Specific fix for Markedsgt 20 (user's example)
        target_id = uuid.UUID('9524a24b-c585-4e9f-b221-f720386e0e77')
        res = await db.execute(select(Property).where(Property.property_id == target_id))
        p_target = res.scalar_one_or_none()
        
        if p_target:
            print(f"Updating {p_target.address}...")
            p_target.total_area = 1500.0
            p_target.construction_year = 1995
            p_target.energy_label = "B"
            p_target.municipality = "Hadsel"
            p_target.municipality_code = "1866"
            p_target.gnr = 65
            p_target.bnr = 69
            p_target.usage = "Næringseiendom"
            p_target.name = "Markedsgt 20"

        # 1.5 Specific fix for Jernbaneveien 70
        jernbane_id = uuid.UUID('6be94bfd-647d-4f77-9b63-f23dee64db81')
        res = await db.execute(select(Property).where(Property.property_id == jernbane_id))
        p_jern = res.scalar_one_or_none()
        if p_jern:
            print(f"Updating {p_jern.address}...")
            p_jern.total_area = 450.0
            p_jern.construction_year = 1985
            p_jern.energy_label = "B"
            p_jern.municipality = "Grue"
            p_jern.municipality_code = "3417"
            p_jern.gnr = 16
            p_jern.bnr = 163
            p_jern.usage = "Næringseiendom"
            p_jern.name = "Jernbaneveien 70"
        
        # 2. General migration for others
        res = await db.execute(select(Property))
        all_props = res.scalars().all()
        
        for p in all_props:
            if p.property_id == target_id:
                continue
                
            ext = p.external_data or {}
            # Map existing external_data to new columns if possible
            if not p.total_area:
                p.total_area = float(ext.get("sqm") or ext.get("total_area") or 0) or None
            if not p.construction_year:
                p.construction_year = int(ext.get("year_built") or ext.get("year") or 0) or None
            if not p.municipality:
                p.municipality = ext.get("city") or p.city
            if not p.gnr:
                p.gnr = int(ext.get("gnr") or 0) or None
            if not p.bnr:
                p.bnr = int(ext.get("bnr") or 0) or None
            if not p.usage:
                p.usage = "Næringseiendom"
            if not p.name:
                p.name = p.address

        # 3. Synchronize unit areas for simple single-unit properties
        from app.domains.core.models.unit import Unit
        for p in all_props:
            res = await db.execute(select(Unit).where(Unit.property_id == p.property_id))
            units = res.scalars().all()
            if len(units) == 1 and units[0].area_sqm == 0.0 and p.total_area:
                units[0].area_sqm = p.total_area
                print(f"Updated unit area for {p.address} to {p.total_area} m2")

        await db.commit()
        print("Metadata population complete.")

if __name__ == "__main__":
    asyncio.run(populate_metadata())
