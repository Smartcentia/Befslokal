
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv(os.path.join(os.getcwd(), 'backend', '.env'))

from app.db.session import SessionLocal
from app.domains.core.models.property import Property
# Import related models to populate registry
try:
    from app.domains.hms.models.risk import RiskAssessment
    from app.domains.hms.models.internal_control import InternalControlCase
    from app.domains.core.models.user import User
except ImportError:
    pass

from sqlalchemy import select

async def check():
    async with SessionLocal() as db:
        # Check Tærudgata 16
        print("Checking Tærudgata 16...")
        result = await db.execute(select(Property).where(Property.name.like('%Tærudgata 16%')))
        p = result.scalars().first()
        if p:
            print(f'Property: {p.name}')
            fin = p.external_data.get('financials', {})
            print(f'Financials: {fin}')
        else:
            print('Property "Tærudgata 16" not found')

        # Check total updated
        print("\nChecking properties with manual_text_import_jan_2026...")
        # Note: querying JSON is database specific, here we just iterate as quick check or assume filtering isn't needed for count
        result = await db.execute(select(Property))
        all_props = result.scalars().all()
        count = 0
        for p in all_props:
            if p.external_data and p.external_data.get('financials', {}).get('data_source') == 'manual_text_import_jan_2026':
                count += 1
        print(f"Total properties updated: {count}")

if __name__ == "__main__":
    asyncio.run(check())
