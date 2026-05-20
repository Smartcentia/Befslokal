
import asyncio
import sys
import os
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

# Import all models to ensure registry is populated
try:
    from app.domains.core.models.user import User
    from app.domains.hms.models.risk import RiskAssessment
    from app.domains.hms.models.internal_control import InternalControlCase
    from app.domains.core.models.property import Property
except ImportError as e:
    print(f"Import Error: {e}")
    # Try importing with package prefix if running as script
    from backend.app.domains.core.models.user import User
    from backend.app.domains.hms.models.risk import RiskAssessment
    from backend.app.domains.hms.models.internal_control import InternalControlCase
    from backend.app.domains.core.models.property import Property


async def list_properties():
    async with SessionLocal() as db:
        stmt = select(Property.name, Property.address, Property.property_id, Property.external_data)
        result = await db.execute(stmt)
        props = result.all()
        
        print(f"Total Properties: {len(props)}")
        print("--- Mapping Candidates ---")
        for p in props:
            # Check if this looks like a master property (e.g. has GNR/BNR or is not just an import)
            # For now just print all
            ext = p.external_data or {}
            is_financial_source = 'financials' in ext
            # Extract dim2 if present
            dim2 = ext.get('Dim 2') or ext.get('Dim 2(T)')
            if 'financials' in ext:
                fin = ext['financials']
                if isinstance(fin, dict):
                    dim2 = fin.get('dim_2_original') or dim2
            
            print(f"ID: {p.property_id} | Name: {p.name} | Address: {p.address} | Financials: {is_financial_source} | Dim2: {dim2}")

if __name__ == "__main__":
    asyncio.run(list_properties())
