
import asyncio
import sys
import os
import json
from sqlalchemy import select

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
from app.domains.core.models.user import User
from app.domains.hms.models.risk import RiskAssessment
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.property import Property

async def check():
    async with SessionLocal() as db:
        # Fetch Kantarellveien matches
        res1 = await db.execute(select(Property).filter(Property.name.ilike('%Kantarellveien%')))
        props = res1.scalars().all()
        print(f'--- Kantarellveien matches ({len(props)}) ---')
        for p in props:
            print(f"Name: {p.name}")
            print(json.dumps(p.external_data, indent=2))

        # Fetch Ramsrudveien 32 (Hidden?)
        res2 = await db.execute(select(Property).filter(Property.name == 'Ramsrudveien 32'))
        p2 = res2.scalars().first()
        print('--- Ramsrudveien 32 ---')
        if p2:
            print(f"Name: {p2.name}")
            print(json.dumps(p2.external_data, indent=2))
        else:
            print('Not Found')

if __name__ == '__main__': 
    asyncio.run(check())
