"""
Quick script to add Frank as admin user
"""
import asyncio
from app.db.session import SessionLocal
from app.domains.core.models.user import User, UserRole
from sqlalchemy import select

async def main():
    async with SessionLocal() as db:
        # Check if user exists
        stmt = select(User).where(User.email == 'frankvevle@hotmail.com')
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f'✅ User already exists: {existing.email} with role {existing.role}')
            if existing.role != UserRole.ADMIN:
                existing.role = UserRole.ADMIN
                await db.commit()
                print(f'✅ Updated {existing.email} to ADMIN role')
            return
        
        # Create admin user
        user = User(
            email='frankvevle@hotmail.com',
            name='Frank Vevle',
            role=UserRole.ADMIN
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f'✅ Created user: {user.email} with role {user.role}')

if __name__ == '__main__':
    asyncio.run(main())
