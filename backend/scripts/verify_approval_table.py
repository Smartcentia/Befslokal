import asyncio
from sqlalchemy import text
from app.db.session import engine

async def check_table():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT to_regclass('public.pending_script_executions');"))
        table_exists = result.scalar()
        print(f"Table 'pending_script_executions': {table_exists}")

if __name__ == "__main__":
    asyncio.run(check_table())
