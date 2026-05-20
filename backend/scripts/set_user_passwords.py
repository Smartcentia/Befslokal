"""
Set passwords for all users in the database
Default password: test123
"""
import asyncio
import os
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all models first to ensure relationships are configured
import app.db.base  # This imports all models
from app.domains.core.models.user import User
from app.core.security.pwd import get_password_hash

async def set_passwords():
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
    
    # Default password for all test users
    default_password = "test123"
    hashed_password = get_password_hash(default_password)
    
    try:
        async with async_session() as session:
            # Get all users
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()
            
            if not users:
                print("❌ No users found in database!")
                return
            
            print(f"✅ Found {len(users)} users")
            print(f"🔐 Setting password '{default_password}' for all users...")
            
            updated_count = 0
            for user in users:
                if not user.hashed_password:
                    user.hashed_password = hashed_password
                    user.is_active = True  # Ensure user is active
                    updated_count += 1
                    print(f"  ✓ {user.email}")
            
            await session.commit()
            
            print(f"\n✅ Successfully set passwords for {updated_count} users!")
            print(f"\n🔑 Login credentials:")
            print(f"   Email: Any user email (e.g., admin@bufdir.no)")
            print(f"   Password: {default_password}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(set_passwords())
