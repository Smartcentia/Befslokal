"""
Simple script to create test users via backend API
This can be run from local machine against production backend
"""
import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.domains.core.models.user import User, UserRole

async def create_test_users():
    async with SessionLocal() as db:
        try:
            # Check if users exist
            stmt = select(User).where(User.email == "admin@bufdir.no")
            result = await db.execute(stmt)
            
            if result.scalar_one_or_none():
                print("✅ Test users already exist!")
                return
            
            # Create minimal test users
            users = [
                User(email="admin@bufdir.no", name="System Admin", role=UserRole.ADMIN, region="National"),
                User(email="region.ost@bufetat.no", name="Regionssjef Øst", role=UserRole.REGIONAL_MANAGER, region="Region Øst"),
                User(email="leder.lillestrom@bufetat.no", name="Driftsleder Lillestrøm", role=UserRole.PROPERTY_MANAGER, region="Region Øst"),
                User(email="vaktmester.oslo@bufetat.no", name="Vaktmester Oslo Sentrum", role=UserRole.PROPERTY_MANAGER, region="Region Øst"),
                User(email="vaktmester.lillestrom@bufetat.no", name="Vaktmester Lillestrøm", role=UserRole.PROPERTY_MANAGER, region="Region Øst"),
                User(email="vaktmester.drammen@bufetat.no", name="Vaktmester Drammen", role=UserRole.PROPERTY_MANAGER, region="Region Øst"),
                User(email="vaktmester.fredrikstad@bufetat.no", name="Vaktmester Fredrikstad", role=UserRole.PROPERTY_MANAGER, region="Region Øst"),
            ]
            
            for user in users:
                db.add(user)
            
            await db.commit()
            print(f"✅ Created {len(users)} test users successfully!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(create_test_users())
