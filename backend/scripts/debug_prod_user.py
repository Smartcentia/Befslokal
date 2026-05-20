import asyncio
import logging
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Setup path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings
from app.core.security.pwd import verify_password, get_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_user():
    print(f"DEBUG: Checking DATABASE_URL from settings...")
    db_url = settings.DATABASE_URL
    if not db_url:
        print("❌ DATABASE_URL is missing in settings!")
        return

    # Mask password
    safe_url = db_url.split("@")[-1] if "@" in db_url else "..."
    print(f"DEBUG: Connecting to DB ending in ...@{safe_url}")

    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        email = "frankvevle@gmail.com"
        print(f"DEBUG: Searching for user {email} (Raw SQL)...")
        
        # Raw Select
        result = await conn.execute(
            text("SELECT user_id, email, hashed_password, is_active FROM users WHERE email = :email"),
            {"email": email}
        )
        row = result.fetchone()

        if not row:
            print(f"❌ User {email} NOT FOUND in this database.")
        else:
            # row is a tuple-like object. Access by index or name (depending on driver, usually indices for asyncpg raw but keys work too in sqlalchemy row)
            # user_id=0, email=1, hashed_password=2, is_active=3
            user_id = row[0]
            current_hash = row[2]
            is_active = row[3]
            
            print(f"✅ User found: ID={user_id}")
            print(f"   - Is Active: {is_active}")
            print(f"   - Hashed Password Field: {current_hash[:10] if current_hash else 'NONE'}")
            
            should_update = False
            
            if not current_hash:
                print("❌ User has NO password set.")
                should_update = True
            else:
                 # Verify
                is_valid = verify_password("Sureminer_6533", current_hash)
                if is_valid:
                    print("✅ Password 'Sureminer_6533' validates CORRECTLY against DB hash.")
                else:
                    print("❌ Password 'Sureminer_6533' FAILED validation against DB hash.")
                    should_update = True
            
            if should_update:
                print("   -> Attempting to SET/RESET password to 'Sureminer_6533'...")
                new_hash = get_password_hash("Sureminer_6533")
                
                await conn.execute(
                    text("UPDATE users SET hashed_password = :h WHERE user_id = :uid"),
                    {"h": new_hash, "uid": user_id}
                )
                print("✅ Password updated in DB.")

    await engine.dispose()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_user())
