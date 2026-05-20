import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import select

# Load environment variables
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))
load_dotenv(os.path.join(os.getcwd(), '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.party import Party
from app.domains.core.models.contract import Contract
from app.domains.core.models.property import Property
from app.domains.core.models.center import Center
from app.domains.core.models.unit import Unit
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.hms.models.checklist import ChecklistTemplate, ChecklistExecution
from app.models.file_meta import FileMeta
from app.domains.core.models.user import User
from app.domains.core.models.audit import AuditLog

async def check():
    async with SessionLocal() as db:
        properties = await db.execute(select(Property))
        contracts = await db.execute(select(Contract))
        parties = await db.execute(select(Party))
        
        prop_list = properties.scalars().all()
        cont_list = contracts.scalars().all()
        party_list = parties.scalars().all()
        
        print(f"Properties: {len(prop_list)}")
        print(f"Contracts: {len(cont_list)}")
        print(f"Parties: {len(party_list)}")
        
        print("\nChecking AIMO PARK specifically:")
        aimo = (await db.execute(select(Party).where(Party.name == 'AIMO PARK NORWAY AS'))).scalar_one_or_none()
        if aimo:
            print(f"Name: {aimo.name}")
            print(f"Orgnr: {aimo.orgnr}")
            print(f"External Data: {aimo.external_data}")
            # Check for generic source field if it exists (not in model but maybe in dict representation)
            print(f"Source in External Data: {aimo.external_data.get('source') if aimo.external_data else 'N/A'}")
        else:
            print("AIMO PARK not found")

if __name__ == "__main__":
    asyncio.run(check())
