"""
Script to create 5 admin users with secure passwords.
Users are created with ADMIN role and email_verified=True (no email confirmation needed).
"""
import sys
import os
import asyncio
import secrets
import string
from pathlib import Path
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# IMPORTANT: Import base.py first to register all models with SQLAlchemy
# This ensures that relationships can resolve properly
from app.db import base  # noqa: F401

from sqlalchemy import select
from app.db.session import SessionLocal
from app.domains.core.models.user import User, UserRole

# Admin users to create
ADMIN_USERS = [
    {
        "email": "oystein.moller.frich@bufdir.no",
        "name": "Øystein Møller Frich"
    },
    {
        "email": "ove.braten@bufdir.no",
        "name": "Ove Bråten"
    },
    {
        "email": "larstony.laberget@bufdir.no",
        "name": "Larstony Laberget"
    },
    {
        "email": "frankvevle@gmail.com",
        "name": "Frank Vevle"
    },
    {
        "email": "frankvevle@hotmail.com",
        "name": "Frank Vevle"
    }
]


def generate_secure_password(length=16):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


async def create_admin_users():
    """Create admin users in the database."""
    async with SessionLocal() as db:
        try:
            created_users = []
            updated_users = []
            passwords = {}
            
            for user_data in ADMIN_USERS:
                email = user_data["email"].lower().strip()
                name = user_data["name"]
                
                # Check if user already exists
                stmt = select(User).where(User.email == email)
                result = await db.execute(stmt)
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    # Update existing user to ADMIN if not already
                    if existing_user.role != UserRole.ADMIN:
                        existing_user.role = UserRole.ADMIN
                        existing_user.email_verified = True
                        await db.commit()
                        updated_users.append(email)
                        print(f"✅ Updated {email} to ADMIN role and verified email")
                    else:
                        print(f"ℹ️  User {email} already exists as ADMIN")
                else:
                    # Create new admin user
                    password = generate_secure_password()
                    passwords[email] = password
                    
                    user = User(
                        email=email,
                        name=name,
                        role=UserRole.ADMIN,
                        email_verified=True,  # No email confirmation needed
                        mfa_enabled=True,
                        region=None  # Admin has no specific region
                    )
                    
                    db.add(user)
                    await db.commit()
                    await db.refresh(user)
                    created_users.append(email)
                    print(f"✅ Created admin user: {email}")
            
            # Print password summary
            if passwords:
                print("\n" + "="*80)
                print("ADMIN USER PASSWORDS - SAVE THESE SECURELY!")
                print("="*80)
                for email, password in passwords.items():
                    print(f"\nEmail: {email}")
                    print(f"Password: {password}")
                print("\n" + "="*80)
                print(f"\n✅ Created {len(created_users)} new admin users")
                print(f"✅ Updated {len(updated_users)} existing users to ADMIN")
                print(f"\n⚠️  IMPORTANT: Share these passwords securely with the users!")
            else:
                print(f"\n✅ All users already exist as ADMIN")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("Creating admin users...")
    asyncio.run(create_admin_users())
    print("\n✅ Done!")
