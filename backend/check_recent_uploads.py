
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select
from datetime import datetime, timedelta
import dotenv

dotenv.load_dotenv("backend/.env")

# Manually define FileMeta model minimal structure for query
from app.models.file_meta import FileMeta
from app.db.base import Base

async def check_recent():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set")
        return

    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Check for files uploaded in the last 1 hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        print(f"Checking for files uploaded after: {one_hour_ago}")
        
        # Note: uploaded_at might be timezone naive or aware depending on implementation
        stmt = select(FileMeta).where(FileMeta.created_at > one_hour_ago).order_by(FileMeta.created_at.desc())
        result = await db.execute(stmt)
        files = result.scalars().all()
        
        if not files:
            print("No new files found in the last hour.")
        else:
            print(f"Found {len(files)} new files:")
            for f in files:
                print(f" - ID: {f.file_id}")
                # Filename is not a column, derive from path
                filename = os.path.basename(f.path)
                print(f"   Filename: {filename}")
                print(f"   Path: {f.path}")
                print(f"   Created: {f.created_at}")
                print("--------------------------------")

if __name__ == "__main__":
    asyncio.run(check_recent())
