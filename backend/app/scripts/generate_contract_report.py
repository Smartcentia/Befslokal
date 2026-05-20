
import asyncio
import sys
import os
import json
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

def get_database_url():
    # Try reading .env file manually
    env_path = os.path.join(os.getcwd(), 'backend', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip('"').strip("'")
    return os.environ.get("DATABASE_URL")

os.environ["DATABASE_URL"] = get_database_url()

from app.db.session import SessionLocal
# Import ALL models
try:
    from app.domains.core.models.user import User
    from app.domains.hms.models.risk import RiskAssessment
    from app.domains.hms.models.internal_control import InternalControlCase
    from app.domains.core.models.property import Property
    from app.domains.core.models.party import Party
    from app.domains.core.models.contract import Contract
    from app.domains.core.models.unit import Unit # Required for contract.unit relationship
except ImportError:
     from backend.app.domains.core.models.user import User
     from backend.app.domains.hms.models.risk import RiskAssessment
     from backend.app.domains.hms.models.internal_control import InternalControlCase
     from backend.app.domains.core.models.property import Property
     from backend.app.domains.core.models.party import Party
     from backend.app.domains.core.models.contract import Contract
     from backend.app.domains.core.models.unit import Unit

async def generate_report():
    async with SessionLocal() as db:
        # Fetch all contracts with related Unit/Property
        # Note: Contract -> Unit -> Property
        stmt = select(Contract).options(
            selectinload(Contract.unit).selectinload(Unit.property)
        )
        result = await db.execute(stmt)
        contracts = result.scalars().all()
        
        headers = ["Kontrakt ID", "Status", "Eiendom", "Adresse", "Periode"]
        rows = []
        
        for c in contracts:
            prop_name = "N/A"
            prop_addr = "N/A"
            if c.unit and c.unit.property:
                prop_name = c.unit.property.name
                prop_addr = c.unit.property.address or ""
            
            # Period extracting
            periods_txt = "N/A"
            if c.periods:
                 # simplistic
                 periods_txt = str(c.periods)
            
            rows.append(f"| {c.contract_id} | {c.status} | {prop_name} | {prop_addr} | {periods_txt} |")

        # Write MD
        md_content = f"| {' | '.join(headers)} |\n| {' | '.join(['---']*len(headers))} |\n"
        md_content += "\n".join(rows)
        
        print(md_content)

if __name__ == '__main__': 
    asyncio.run(generate_report())
