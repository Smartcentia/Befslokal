#!/usr/bin/env python3
"""
Export all properties and contracts to CSV for easy viewing.
"""
import sys
import os
from pathlib import Path
import asyncio
import csv
from sqlalchemy import select

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

async def export_properties_contracts():
    print("📊 Eksporterer eiendommer og kontrakter...")
    
    async with SessionLocal() as db:
        # Get all contracts with related data
        result = await db.execute(
            select(Contract, Unit, Property, Party)
            .join(Unit, Contract.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
            .outerjoin(Party, Contract.party_id == Party.party_id)
            .order_by(Property.address, Contract.start_date)
        )
        
        rows = result.all()
        
        # Write to CSV
        output_file = '/tmp/eiendommer_kontrakter.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            
            # Header
            writer.writerow([
                'Adresse',
                'Postnr',
                'Sted',
                'Region',
                'Kommune',
                'Areal (m²)',
                'Gnr/Bnr',
                'Utleier',
                'Org.nr',
                'Startdato',
                'Sluttdato',
                'Status',
                'Årlig leie (NOK)',
                'Estimert',
                'Kontrakt ID'
            ])
            
            # Data rows
            for contract, unit, prop, party in rows:
                rent = 0
                estimated = ''
                if contract.amount:
                    rent = contract.amount.get('amount_per_year', 0)
                    if contract.amount.get('estimated'):
                        if contract.amount.get('used_default_area'):
                            estimated = 'Ja (std areal)'
                        else:
                            estimated = 'Ja'
                
                writer.writerow([
                    prop.address or '',
                    prop.postal_code or '',
                    prop.city or '',
                    prop.region or '',
                    prop.municipality or '',
                    f"{prop.total_area:.0f}" if prop.total_area else '',
                    f"{prop.gnr}/{prop.bnr}" if prop.gnr and prop.bnr else '',
                    party.name if party else '',
                    party.orgnr if party else '',
                    contract.start_date.strftime('%Y-%m-%d') if contract.start_date else '',
                    contract.end_date.strftime('%Y-%m-%d') if contract.end_date else '',
                    contract.status or '',
                    f"{rent:.0f}",
                    estimated,
                    str(contract.contract_id)
                ])
        
        print(f"\n✅ Eksportert {len(rows)} kontrakter til {output_file}")
        print(f"\nÅpne filen med:")
        print(f"  open {output_file}")
        print(f"\nEller vis i terminal:")
        print(f"  cat {output_file} | head -50")

if __name__ == "__main__":
    asyncio.run(export_properties_contracts())
