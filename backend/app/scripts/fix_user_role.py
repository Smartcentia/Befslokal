"""
Quick script to update a user's role to ADMIN
Run this to fix your user role
"""
import asyncio
import sys
from sqlalchemy import select, update
from app.db.session import SessionLocal
from app.domains.core.models.user import User, UserRole

async def update_user_role(email: str, new_role: UserRole):
    async with SessionLocal() as db:
        try:
            # Find user
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User {email} not found!")
                return
            
            print(f"📋 Current: {user.email} → {user.role}")
            
            # Update role
            user.role = new_role
            await db.commit()
            
            print(f"✅ Updated: {user.email} → {user.role}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_user_role.py <email> [role]")
        print("Example: python fix_user_role.py frank@example.com ADMIN")
        sys.exit(1)
    
    email = sys.argv[1]
    role = UserRole.ADMIN if len(sys.argv) < 3 else UserRole[sys.argv[2]]
    
    asyncio.run(update_user_role(email, role))
