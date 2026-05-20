import asyncio
import os
import sys
from sqlalchemy import select, func

# Add backend to path
current_file = os.path.abspath(__file__)
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file))) # .../backend
project_root = os.path.dirname(backend_dir) # .../KNOWME

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load ENV for DB
def get_database_url():
    env_path = os.path.join(backend_dir, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip('"').strip("'")
    return os.environ.get("DATABASE_URL")

db_url = get_database_url()
if db_url:
    os.environ["DATABASE_URL"] = db_url

try:
    from app.db.session import SessionLocal
    from app.domains.core.models.property import Property
    from app.domains.core.models.contract import Contract
    from app.domains.core.models.unit import Unit
    from app.domains.core.models.party import Party
    from app.domains.core.models.user import User
    from app.domains.hms.models.risk import RiskAssessment
    from app.domains.hms.models.internal_control import InternalControlCase
except ImportError:
    from backend.app.db.session import SessionLocal
    from backend.app.domains.core.models.property import Property
    from backend.app.domains.core.models.contract import Contract
    from backend.app.domains.core.models.unit import Unit
    from backend.app.domains.core.models.party import Party
    from backend.app.domains.core.models.user import User
    from backend.app.domains.hms.models.risk import RiskAssessment
    from backend.app.domains.hms.models.internal_control import InternalControlCase

async def count_merged():
    async with SessionLocal() as db:
        stmt = select(func.count()).select_from(Property).where(Property.name.like("MERGED%"))
        result = await db.execute(stmt)
        count = result.scalar()
        
        print(f"Total Merged Properties: {count}")
        
        # List a few
        stmt_list = select(Property).where(Property.name.like("MERGED%")).limit(10)
        res_list = await db.execute(stmt_list)
        props = res_list.scalars().all()
        for p in props:
            print(f" - {p.name}")

if __name__ == "__main__":
    asyncio.run(count_merged())
