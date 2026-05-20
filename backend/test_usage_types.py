import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import os

from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv(".env.local", override=True)

from app.domains.core.models.property import Property as PropertyModel
from app.domains.core.models.user import User

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def test():
    try:
        async with async_session() as db:
            query = select(PropertyModel.usage).where(PropertyModel.usage != None).distinct().order_by(PropertyModel.usage)
            result = await db.execute(query)
            types = [r[0] for r in result.all() if r[0]]
            print("usage types:", types)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    asyncio.run(test())
