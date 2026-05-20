
import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.generated_tool import GeneratedTool

async def check_tools():
    async with SessionLocal() as db:
        result = await db.execute(select(GeneratedTool))
        tools = result.scalars().all()
        print(f"🛠️ Found {len(tools)} generated tools:")
        for t in tools:
            print(f"- {t.name} (Status: {t.status})")
            print(f"  Desc: {t.description}")

if __name__ == "__main__":
    asyncio.run(check_tools())
