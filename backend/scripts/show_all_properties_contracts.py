#!/usr/bin/env python3
"""
Show all properties and their associated contracts.
"""
import sys
import os
from pathlib import Path
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import joinedload

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party

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

async def show_all_properties_and_contracts():
    print("🏢 ALLE EIENDOMMER OG KONTRAKTER")
    print("=" * 80)
    
    async with SessionLocal() as db:
        # Get all properties
        result = await db.execute(
            select(Property).order_by(Property.address)
        )
        properties = result.scalars().all()
        
        print(f"\nTotalt {len(properties)} eiendommer\n")
        
        total_contracts = 0
        
        for prop in properties:
            # Property header
            print(f"\n{'='*80}")
            print(f"📍 {prop.address}")
            if prop.city:
                print(f"   {prop.postal_code} {prop.city}")
            if prop.region:
                print(f"   Region: {prop.region}")
            if prop.municipality:
                print(f"   Kommune: {prop.municipality}")
            if prop.total_area:
                print(f"   Areal: {prop.total_area:,.0f} m²")
            if prop.gnr and prop.bnr:
                print(f"   Gnr/Bnr: {prop.gnr}/{prop.bnr}")
            
            # Get units for this property
            units_result = await db.execute(
                select(Unit).where(Unit.property_id == prop.property_id)
            )
            units = units_result.scalars().all()
            
            # Get all contracts for this property
            property_contracts = []
            for unit in units:
                contracts_result = await db.execute(
                    select(Contract).options(
                        joinedload(Contract.party)
                    ).where(Contract.unit_id == unit.unit_id)
                )
                property_contracts.extend(contracts_result.scalars().all())
            
            if not property_contracts:
                print(f"\n   ⚠️  Ingen kontrakter")
                continue
            
            print(f"\n   📋 {len(property_contracts)} kontrakt(er):")
            
            for i, contract in enumerate(property_contracts, 1):
                total_contracts += 1
                
                # Contract details
                print(f"\n   [{i}] Kontrakt ID: {contract.contract_id}")
                
                # Landlord
                if contract.party:
                    print(f"       Utleier: {contract.party.name}")
                    if contract.party.org_number:
                        print(f"       Org.nr: {contract.party.org_number}")
                
                # Dates
                start = contract.start_date.strftime('%Y-%m-%d') if contract.start_date else 'N/A'
                end = contract.end_date.strftime('%Y-%m-%d') if contract.end_date else 'N/A'
                print(f"       Periode: {start} → {end}")
                print(f"       Status: {contract.status}")
                
                # Amount
                if contract.amount:
                    rent = contract.amount.get('amount_per_year', 0)
                    currency = contract.amount.get('currency', 'NOK')
                    estimated = contract.amount.get('estimated', False)
                    used_default = contract.amount.get('used_default_area', False)
                    
                    estimate_flag = ""
                    if estimated:
                        if used_default:
                            estimate_flag = " (estimert med standard areal)"
                        else:
                            estimate_flag = " (estimert)"
                    
                    print(f"       Årlig leie: {rent:,.0f} {currency}{estimate_flag}")
                else:
                    print(f"       Årlig leie: Ikke oppgitt")
        
        print(f"\n{'='*80}")
        print(f"\n📊 OPPSUMMERING:")
        print(f"   Totalt eiendommer: {len(properties)}")
        print(f"   Totalt kontrakter: {total_contracts}")
        print(f"   Gjennomsnitt kontrakter per eiendom: {total_contracts/len(properties):.1f}")

if __name__ == "__main__":
    asyncio.run(show_all_properties_and_contracts())
