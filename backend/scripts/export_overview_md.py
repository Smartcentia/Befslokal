import asyncio
import sys
import os

# Add backend directory to path so we can import app modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.core.models.unit import Unit
from app.domains.core.models.contract import Contract
from app.domains.core.models.party import Party
# Import other models to ensure SQLAlchemy registry is populated
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.user import User

async def main():
    async with SessionLocal() as session:
        # Fetch all properties with their units and contracts
        # Because the relationship direction is mainly Contract -> Unit -> Property
        # We might need to query Property and reverse join, or just query Contracts.
        # However, we want ALL properties, even empty ones.
        
        # We can't easily rely on reverse relationships if they aren't set up fully in the models we saw.
        # Property.units? Property.contracts? 
        # Unit has `property_id`.
        # Contract has `unit_id`.
        
        # Let's query Properties and load Units. 
        # But wait, Unit doesn't have `contracts` relationship explicitly defined in the snippet I saw?
        # Let's check Unit again.
        # Unit: `property = relationship("Property", lazy="selectin")`
        # It does NOT have a reverse relationship to Contract in the snippet.
        # Contract: `unit = relationship("Unit")`.
        # So we have to join manually or query Contracts and map them.
        
        # Better approach:
        # 1. Fetch all Properties.
        # 2. Fetch all Units.
        # 3. Fetch all Contracts (with Parties).
        # 4. Join in memory.
        
        stmt_props = select(Property)
        result_props = await session.execute(stmt_props)
        properties = result_props.scalars().all()
        
        stmt_units = select(Unit)
        result_units = await session.execute(stmt_units)
        units = result_units.scalars().all()
        
        stmt_contracts = select(Contract).options(selectinload(Contract.party))
        result_contracts = await session.execute(stmt_contracts)
        contracts = result_contracts.scalars().all()
        
        # Organize in memory
        prop_map = {p.property_id: p for p in properties}
        unit_map = {u.unit_id: u for u in units}
        
        # Build structure: Property -> [Unit -> [Contract]]
        data_rows = []
        
        # Map units to properties
        prop_units = {p.property_id: [] for p in properties}
        for u in units:
            if u.property_id in prop_units:
                prop_units[u.property_id].append(u)
                
        # Map contracts to units
        unit_contracts = {u.unit_id: [] for u in units}
        for c in contracts:
            if c.unit_id in unit_contracts:
                unit_contracts[c.unit_id].append(c)
                
        # Generate Rows
        # Columns: Eiendom, Enhet, Leietaker, Kontrakt ID, Beløp, Status
        
        for prop in properties:
            p_units = prop_units.get(prop.property_id, [])
            
            if not p_units:
                # Property with no units
                data_rows.append([prop.name or prop.address, "-", "-", "-", "-", "-"])
                continue
                
            for unit in p_units:
                u_contracts = unit_contracts.get(unit.unit_id, [])
                
                if not u_contracts:
                    # Unit with no contracts
                    data_rows.append([prop.name or prop.address, unit.purpose or "N/A", "-", "-", "-", "-"])
                    continue
                    
                for contract in u_contracts:
                    party_name = contract.party.name if contract.party else "Ukjent"
                    amount = "N/A"
                    if contract.amount:
                        if isinstance(contract.amount, dict):
                            amount = str(contract.amount.get("amount_per_year", "N/A"))
                        else:
                            amount = str(contract.amount)
                            
                    data_rows.append([
                        prop.name or prop.address or "Ukjent",
                        unit.purpose or "N/A",
                        party_name,
                        str(contract.contract_id)[:8] + "...",
                        amount,
                        contract.status or "N/A"
                    ])

        # Sort by Property Name
        data_rows.sort(key=lambda x: x[0])
        
        # Output Markdown Table
        headers = ["Eiendom", "Enhet", "Leietaker", "Kontrakt", "Beløp (År)", "Status"]
        
        # Calculate widths
        widths = [len(h) for h in headers]
        for row in data_rows:
            for i, val in enumerate(row):
                widths[i] = max(widths[i], len(str(val)))
                
        # Print Table
        header_line = "| " + " | ".join(f"{h:<{w}}" for h, w in zip(headers, widths)) + " |"
        sep_line = "| " + " | ".join("-" * w for w in widths) + " |"
        
        print(header_line)
        print(sep_line)
        for row in data_rows:
            print("| " + " | ".join(f"{str(val):<{w}}" for val, w in zip(row, widths)) + " |")

if __name__ == "__main__":
    asyncio.run(main())
