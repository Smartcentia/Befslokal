
import asyncio
import sys
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.generated_tool import GeneratedTool

async def approve_tool(name):
    async with SessionLocal() as db:
        result = await db.execute(select(GeneratedTool).where(GeneratedTool.name == name))
        tool = result.scalar_one_or_none()
        
        if not tool:
            print(f"❌ Tool '{name}' not found.")
            return

        tool.status = 'active'
        await db.commit()
        print(f"✅ Tool '{name}' is now ACTIVE. Restart backend to load it.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/approve_tool.py <tool_name|all>")
        sys.exit(1)
    
    arg = sys.argv[1]
    if arg == "all":
        import asyncio
        async def approve_all():
             async with SessionLocal() as db:
                result = await db.execute(select(GeneratedTool).where(GeneratedTool.status == 'pending'))
                tools = result.scalars().all()
                for t in tools:
                    t.status = 'active'
                    print(f"✅ Approved: {t.name}")
                await db.commit()
        asyncio.run(approve_all())
    else:
        asyncio.run(approve_tool(arg))
