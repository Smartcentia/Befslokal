"""
Seed test users directly via SQLAlchemy ORM
"""
import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import uuid
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.domains.core.models.user import User, UserRole

async def seed_users():
    # Get DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Try to load from .env
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DATABASE_URL="):
                        database_url = line.split("=", 1)[1].strip('"').strip("'")
                        break
    
    if not database_url:
        print("❌ DATABASE_URL not found!")
        return
    
    print(f"📋 Connecting to database...")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # Check if admin already exists
            stmt = select(User).where(User.email == "admin@bufdir.no")
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                print("✅ Users already exist - skipping seed")
                # Show counts
                stmt = select(User)
                result = await session.execute(stmt)
                all_users = result.scalars().all()
                print(f"📊 Total users: {len(all_users)}")
                return
            
            print("✅ Connected! Creating test users...")
            
            # Create users
            test_users = [
                # Admin
                User(
                    user_id=str(uuid.uuid4()),
                    email="admin@bufdir.no",
                    name="System Admin",
                    role=UserRole.ADMIN,
                    region="National",
                    created_at=datetime.utcnow()
                ),
                # Regional Managers
                User(
                    user_id=str(uuid.uuid4()),
                    email="region.ost@bufetat.no",
                    name="Regionssjef Øst",
                    role=UserRole.REGIONAL_MANAGER,
                    region="Region Øst",
                    created_at=datetime.utcnow()
                ),
                User(
                    user_id=str(uuid.uuid4()),
                    email="region.vest@bufetat.no",
                    name="Regionssjef Vest",
                    role=UserRole.REGIONAL_MANAGER,
                    region="Region Vest",
                    created_at=datetime.utcnow()
                ),
                User(
                    user_id=str(uuid.uuid4()),
                    email="region.nord@bufetat.no",
                    name="Regionssjef Nord",
                    role=UserRole.REGIONAL_MANAGER,
                    region="Region Nord",
                    created_at=datetime.utcnow()
                ),
                # Area Managers
                User(
                    user_id=str(uuid.uuid4()),
                    email="leder.oslo@bufetat.no",
                    name="Driftsleder Oslo",
                    role=UserRole.PROPERTY_MANAGER,
                    region="Region Øst",
                    created_at=datetime.utcnow()
                ),
                User(
                    user_id=str(uuid.uuid4()),
                    email="leder.lillestrom@bufetat.no",
                    name="Driftsleder Lillestrøm",
                    role=UserRole.PROPERTY_MANAGER,
                    region="Region Øst",
                    created_at=datetime.utcnow()
                ),
                User(
                    user_id=str(uuid.uuid4()),
                    email="leder.drammen@bufetat.no",
                    name="Driftsleder Drammen",
                    role=UserRole.PROPERTY_MANAGER,
                    region="Region Øst",
                    created_at=datetime.utcnow()
                ),
                # Caretakers
                User(
                    user_id=str(uuid.uuid4()),
                    email="vaktmester.oslo.sentrum@bufetat.no",
                    name="Vaktmester Oslo Sentrum",
                    role=UserRole.PROPERTY_MANAGER,
                    region="Region Øst",
                    created_at=datetime.utcnow()
                ),
                User(
                    user_id=str(uuid.uuid4()),
                    email="vaktmester.oslo.nord@bufetat.no",
                    name="Vaktmester Oslo Nord",
                    role=UserRole.PROPERTY_MANAGER,
                    region="Region Øst",
                    created_at=datetime.utcnow()
                ),
                User(
                    user_id=str(uuid.uuid4()),
                    email="vaktmester.lillestrom@bufetat.no",
                    name="Vaktmester Lillestrøm",
                    role=UserRole.PROPERTY_MANAGER,
                    region="Region Øst",
                    created_at=datetime.utcnow()
                ),
                User(
                    user_id=str(uuid.uuid4()),
                    email="vaktmester.drammen@bufetat.no",
                    name="Vaktmester Drammen",
                    role=UserRole.PROPERTY_MANAGER,
                    region="Region Øst",
                    created_at=datetime.utcnow()
                ),
                User(
                    user_id=str(uuid.uuid4()),
                    email="vaktmester.fredrikstad@bufetat.no",
                    name="Vaktmester Fredrikstad",
                    role=UserRole.PROPERTY_MANAGER,
                    region="Region Øst",
                    created_at=datetime.utcnow()
                ),
                User(
                    user_id=str(uuid.uuid4()),
                    email="vaktmester.bergen@bufetat.no",
                    name="Vaktmester Bergen",
                    role=UserRole.PROPERTY_MANAGER,
                    region="Region Vest",
                    created_at=datetime.utcnow()
                ),
                User(
                    user_id=str(uuid.uuid4()),
                    email="vaktmester.stavanger@bufetat.no",
                    name="Vaktmester Stavanger",
                    role=UserRole.PROPERTY_MANAGER,
                    region="Region Vest",
                    created_at=datetime.utcnow()
                ),
                User(
                    user_id=str(uuid.uuid4()),
                    email="vaktmester.tromso@bufetat.no",
                    name="Vaktmester Tromsø",
                    role=UserRole.PROPERTY_MANAGER,
                    region="Region Nord",
                    created_at=datetime.utcnow()
                ),
            ]
            
            session.add_all(test_users)
            await session.commit()
            
            print(f"✅ Successfully seeded {len(test_users)} test users!")
            print("\n📊 User Summary:")
            print(f"  ADMIN: 1 user")
            print(f"  REGIONAL_MANAGER: 3 users")
            print(f"  PROPERTY_MANAGER: 11 users")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_users())
