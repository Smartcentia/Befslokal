#!/usr/bin/env python3
"""
Check properties without cost data (contracts).
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

async def check_properties_without_costs():
    print("🏢 Checking Properties Without Costs")
    print("=" * 60)
    
    async with SessionLocal() as db:
        # Get all properties
        result = await db.execute(select(Property))
        all_properties = result.scalars().all()
        
        print(f"\nTotal properties: {len(all_properties)}")
        
        # Get properties with contracts
        result = await db.execute(
            select(Property.property_id)
            .join(Unit, Unit.property_id == Property.property_id)
            .join(Contract, Contract.unit_id == Unit.unit_id)
            .distinct()
        )
        props_with_contracts = set(row[0] for row in result.all())
        
        print(f"Properties with contracts: {len(props_with_contracts)}")
        
        # Properties without any contracts
        props_without_contracts = []
        for p in all_properties:
            if p.property_id not in props_with_contracts:
                props_without_contracts.append(p)
        
        print(f"Properties WITHOUT contracts: {len(props_without_contracts)}")
        
        if props_without_contracts:
            print(f"\n📋 Examples (first 10):")
            for p in props_without_contracts[:10]:
                print(f"  - {p.address}, {p.city}")
        
        # Properties with contracts but 0 rent
        result = await db.execute(
            select(Property, Contract)
            .join(Unit, Unit.property_id == Property.property_id)
            .join(Contract, Contract.unit_id == Unit.unit_id)
        )
        
        props_with_zero_rent = set()
        for prop, contract in result.all():
            rent = 0
            if contract.amount:
                rent = contract.amount.get('amount_per_year') or 0
            if rent == 0:
                props_with_zero_rent.add((prop.property_id, prop.address, prop.city))
        
        print(f"\nProperties with contracts but 0 NOK rent: {len(props_with_zero_rent)}")
        if props_with_zero_rent:
            print(f"\n📋 Examples (first 10):")
            for pid, addr, city in list(props_with_zero_rent)[:10]:
                print(f"  - {addr}, {city}")

if __name__ == "__main__":
    asyncio.run(check_properties_without_costs())
