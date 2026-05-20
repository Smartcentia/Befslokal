
import asyncio
import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import engine
from app.domains.core.models.user import User

async def list_users():
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(f"User: {u.email} ({u.first_name} {u.last_name}) - ID: {u.user_id} - Role: {u.role}")

if __name__ == "__main__":
    asyncio.run(list_users())
