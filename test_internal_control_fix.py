import asyncio
import os
import sys

# Add backend to path FIRST
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, "backend")
sys.path.append(backend_path)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.core.models.property import Property
from app.domains.core.models.user import User  # Added this import
from sqlalchemy.orm import selectinload

async def test_ic_loading():
    # Use the DB URL from env or fallback
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Try to find it in .env if available
        print("DATABASE_URL not found in environment.")
        return

    # Force asyncpg if not present
    if "postgresql://" in DATABASE_URL and "asyncpg" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

    print(f"Connecting to: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'DB'}")
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        print("Testing InternalControlCase loading with nested selectinload...")
        try:
            stmt = (
                select(InternalControlCase)
                .options(
                    selectinload(InternalControlCase.property).selectinload("managers"),
                    selectinload(InternalControlCase.assigned_user)
                )
                .limit(5)
            )
            result = await session.execute(stmt)
            cases = result.scalars().all()
            
            if cases:
                print(f"✅ Found {len(cases)} cases.")
                for case in cases:
                    print(f"\nCase: {case.title}")
                    if case.property:
                        print(f"Property: {case.property.name}")
                        # Accessing managers - this is where it would crash
                        managers = case.property.managers
                        print(f"Managers: {[m.full_name for m in managers]}")
                        
                        # Verify we can serialize it (simulating Pydantic)
                        from app.schemas.internal_control import InternalControlCase as InternalControlCaseRead
                        try:
                            schema = InternalControlCaseRead.model_validate(case)
                            print("✅ Pydantic serialization SUCCESS")
                        except Exception as pyd_err:
                            print(f"❌ Pydantic serialization FAILED: {pyd_err}")
                    else:
                        print("Property: None")
            else:
                print("⚠️ No cases found to test.")
        except Exception as e:
            print(f"❌ Error during loading: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_ic_loading())
