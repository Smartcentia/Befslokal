import asyncio
import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend path is in sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Load .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from app.db.session import SessionLocal
import app.db.base # Register all models BEFORE importing specific ones
from app.domains.core.models.user import User, UserRole
from app.domains.core.models.property import Property
from app.domains.hms.models.risk import RiskAssessment # Required for relationship resolution
from app.domains.hms.models.internal_control import InternalControlCase # Required for relationship resolution
from sqlalchemy import select
from datetime import datetime
import uuid

def safe_email_from_name(name):
    # Remove special characters, spaces, etc.
    # Lowercase
    clean = name.lower()
    # Replace norwegian chars
    clean = clean.replace("æ", "ae").replace("ø", "o").replace("å", "a")
    # Replace spaces and symbols with dots
    clean = re.sub(r'[^a-z0-9]', '.', clean)
    # Remove multi-dots
    clean = re.sub(r'\.+', '.', clean).strip('.')
    return f"vaktmester.{clean}@bufetat.no"

async def seed_property_users():
    print("📋 Connectivity check...")
    db = SessionLocal()
    try:
        # 1. Get all properties
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        print(f"Found {len(properties)} properties.")
        
        users_created = 0
        users_exist = 0
        
        for prop in properties:
            if not prop.name:
                continue
                
            email = safe_email_from_name(prop.name)
            
            # Check if user exists
            stmt = select(User).where(User.email == email)
            res = await db.execute(stmt)
            existing_user = res.scalar_one_or_none()
            
            if existing_user:
                users_exist += 1
                continue
            
            # Create user
            # Default region to property region or "Region Øst"
            region = prop.region if prop.region else "Region Øst"
            
            new_user = User(
                user_id=uuid.uuid4(),
                email=email,
                name=f"Vaktmester {prop.name}",
                role=UserRole.PROPERTY_MANAGER,
                region=region
            )
            db.add(new_user)
            users_created += 1
            print(f"   Created: {email}")
            
        await db.commit()
        print(f"\n✅ Seeding Complete.")
        print(f"   Existing users skipped: {users_exist}")
        print(f"   New users created: {users_created}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(seed_property_users())
