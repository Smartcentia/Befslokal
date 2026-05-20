#!/usr/bin/env python3
"""
Find the 3 properties with NULL usage and investigate.
"""
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract

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

async def investigate_null_properties():
    print("🔍 Investigating Properties with NULL Usage")
    print("=" * 60)
    
    async with SessionLocal() as db:
        # Find properties with NULL usage
        result = await db.execute(
            select(Property).where(Property.usage == None)
        )
        null_props = result.scalars().all()
        
        print(f"\nFound {len(null_props)} properties with NULL usage:\n")
        
        for prop in null_props:
            print(f"{'='*60}")
            print(f"📍 {prop.address}")
            print(f"   {prop.postal_code} {prop.city}")
            if prop.region:
                print(f"   Region: {prop.region}")
            if prop.municipality:
                print(f"   Kommune: {prop.municipality}")
            if prop.total_area:
                print(f"   Areal: {prop.total_area:,.0f} m²")
            if prop.gnr and prop.bnr:
                print(f"   Gnr/Bnr: {prop.gnr}/{prop.bnr}")
            
            # Check for external data
            if prop.external_data:
                print(f"\n   📋 External Data:")
                for key, value in prop.external_data.items():
                    if isinstance(value, dict):
                        print(f"      {key}: {len(value)} fields")
                    else:
                        print(f"      {key}: {value}")
            
            # Get contracts
            units_result = await db.execute(
                select(Unit).where(Unit.property_id == prop.property_id)
            )
            units = units_result.scalars().all()
            
            contract_count = 0
            for unit in units:
                contracts_result = await db.execute(
                    select(Contract).where(Contract.unit_id == unit.unit_id)
                )
                contracts = contracts_result.scalars().all()
                contract_count += len(contracts)
            
            print(f"\n   📋 Kontrakter: {contract_count}")
            print()

if __name__ == "__main__":
    asyncio.run(investigate_null_properties())
