import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.party import Party
from app.domains.core.models.user import User
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase

OUTPUT_FILE = "backend/docs/generated_enrichment_overview.txt"

async def generate_overview():
    print("Starting enrichment overview generation...")
    
    output_lines = []
    output_lines.append("DATA ENRICHMENT OVERVIEW - GENERATED REPORT")
    output_lines.append("================================================================================")
    
    async with SessionLocal() as db:
        # Fetch all properties
        result = await db.execute(select(Property).order_by(Property.name))
        properties = result.scalars().all()
        print(f"Found {len(properties)} properties.")
        
        for p in properties:
            # Header
            p_name = p.name or "Ukjent Navn"
            p_addr = p.address or "Ukjent Adresse"
            p_muni = p.municipality or ""
            
            output_lines.append(f"EIENDOM: {p_name}")
            output_lines.append(f"ADRESSE: {p_addr} {f'({p_muni})' if p_muni else ''}")
            
            # Basic Info
            details = []
            if p.usage: details.append(f"Bruk: {p.usage}")
            if p.total_area: details.append(f"Areal: {p.total_area} m2")
            if p.construction_year: details.append(f"Byggeår: {p.construction_year}")
            
            if details:
                output_lines.append(f"INFO: {', '.join(details)}")
            
            # 1. Financial Data (Manual/CSV)
            ext = p.external_data or {}
            financials = ext.get('financials', {})
            manual_expenses = financials.get('manual_expenses', [])
            total_manual = financials.get('total_manual_expenses', 0)
            
            if manual_expenses:
                output_lines.append("-" * 40)
                output_lines.append(f"FINANSIELLE UTGIFTER (Totalt: {total_manual:,.2f} NOK):")
                # Group by type for cleaner reading
                by_type = {}
                for exp in manual_expenses:
                    t = exp.get('type', 'Annet')
                    if t not in by_type: by_type[t] = []
                    by_type[t].append(exp)
                
                for t, exps in by_type.items():
                    subtotal = sum(e.get('amount_parsed', 0) for e in exps)
                    output_lines.append(f"  Kategori: {t} (Sum: {subtotal:,.2f})")
                    for e in exps:
                        provider = e.get('provider', 'Ukjent')
                        amt = e.get('amount_parsed', 0)
                        date = e.get('date', '')
                        desc = e.get('description', '')
                        line = f"    - {provider}: {amt:,.2f}"
                        if date: line += f" (Dato: {date})"
                        if desc and desc != 'nan': line += f" [{desc}]"
                        output_lines.append(line)
            else:
                 output_lines.append("-" * 40)
                 output_lines.append("INGEN REGISTRERTE FINANSIELLE UTGIFTER (CSV/MANUELL)")

            # 2. Contracts
            # Fetch contracts linked to this property via Units
            stmt = (
                select(Contract)
                .join(Unit)
                .where(Unit.property_id == p.property_id)
                .options(selectinload(Contract.party), selectinload(Contract.unit))
            )
            c_result = await db.execute(stmt)
            contracts = c_result.scalars().all()
            
            if contracts:
                output_lines.append("-" * 40)
                output_lines.append(f"KONTRAKTER ({len(contracts)}):")
                for c in contracts:
                    party_name = c.party.name if c.party else "Ukjent Motpart"
                    status = c.status or "Ukjent Status"
                    
                    # Try to extract rent amount
                    amount_info = "Ikke spesifisert"
                    if c.amount:
                        # amount might be a dict or value
                        amount_info = str(c.amount)
                    
                    # Periods
                    period_info = ""
                    if c.periods:
                        period_info = f" | Periode: {c.periods}"
                        
                    output_lines.append(f"  - Motpart: {party_name} ({status})")
                    output_lines.append(f"    Beløp: {amount_info}{period_info}")
            else:
                output_lines.append("-" * 40)
                output_lines.append("INGEN REGISTRERTE KONTRAKTER")
                
            output_lines.append("=" * 80)
            output_lines.append("") # Empty line between properties
            
    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_lines))
        
    print(f"Generated overview at: {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(generate_overview())
