"""
Script to grandfather existing users: set email_verified=True and mfa_verified_at.
This should be run once after the migration.
"""
import asyncio
from sqlalchemy import select, update
from app.db.session import SessionLocal
from app.domains.core.models.user import User
from datetime import datetime


async def grandfather_existing_users():
    """
    Set email_verified=True and mfa_verified_at for all existing users.
    This ensures existing users don't need to verify their email.
    """
    async with SessionLocal() as db:
        try:
            # Get all users
            result = await db.execute(select(User))
            users = result.scalars().all()
            
            updated_count = 0
            for user in users:
                # Only update if not already verified
                if not user.email_verified:
                    user.email_verified = True
                    # Set mfa_verified_at to created_at if available, otherwise now
                    if not user.mfa_verified_at:
                        # Try to get created_at from the user object
                        # If created_at doesn't exist, use current time
                        user.mfa_verified_at = datetime.utcnow()
                    updated_count += 1
            
            await db.commit()
            
            print(f"✅ Grandfathered {updated_count} existing users")
            print(f"   Total users: {len(users)}")
            print(f"   Email verified: {updated_count}")
            
        except Exception as e:
            await db.rollback()
            print(f"❌ Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(grandfather_existing_users())
