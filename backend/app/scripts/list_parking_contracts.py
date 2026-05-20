import asyncio
import sys
import os

# Add backend directory to sys.path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import select, or_, func
from app.db.session import SessionLocal
from app.domains.core.models.contract import Contract
from app.domains.core.models.unit import Unit
from app.domains.core.models.property import Property
from app.domains.core.models.party import Party
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User

async def list_parking_contracts():
    async with SessionLocal() as db:
        # Define keywords for parking
        keywords = ["parkering", "garage", "garasje", "bolig", "næring", "lager", "storage"]
        # Filter for only explicit parking keywords for this specific request
        parking_keywords = ["parkering", "garage", "garasje", "p-plass", "park"]


        stmt_all = select(func.count()).select_from(Contract)
        count_all = await db.scalar(stmt_all)
        print(f"Total contracts in DB: {count_all}\n")

        stmt = (
            select(Contract, Unit, Property)
            .join(Unit, Contract.unit_id == Unit.unit_id)
            .join(Property, Unit.property_id == Property.property_id)
        )

        conditions = [Unit.purpose.ilike(f"%{kw}%") for kw in parking_keywords]
        # Also check Property fields
        conditions.extend([Property.address.ilike(f"%{kw}%") for kw in parking_keywords])
        conditions.extend([Property.usage.ilike(f"%{kw}%") for kw in parking_keywords])
        
        stmt = stmt.where(or_(*conditions))
        
        result = await db.execute(stmt)
        rows = result.all()

        print(f"Found {len(rows)} contracts with parking.\n")
        
        print("| Contract ID | Address | Unit Purpose | Status | Source |")
        print("|---|---|---|---|---|")
        
        for contract, unit, prop in rows:
            prop_addr = prop.address if prop else "Unknown"
            purpose = unit.purpose or "N/A"
            status = contract.status or "Unknown"
            
            # Determine source
            sources = []
            if unit.purpose and any(kw in str(unit.purpose).lower() for kw in parking_keywords):
                sources.append("Unit Purpose")
            if prop.address and any(kw in str(prop.address).lower() for kw in parking_keywords):
                sources.append("Property Address")
            if prop.usage and any(kw in str(prop.usage).lower() for kw in parking_keywords):
                sources.append("Property Usage")
            
            source_str = ", ".join(sources) if sources else "Unknown"
            
            print(f"| {contract.contract_id} | {prop_addr} | {purpose} | {status} | {source_str} |")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(list_parking_contracts())
