import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def check_costs():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in result.fetchall()]
        
        if 'gl_transactions' in tables:
            query = """
            SELECT region_name, category, SUM(amount) as total
            FROM gl_transactions
            GROUP BY region_name, category
            ORDER BY region_name, category
            """
            result = await conn.execute(text(query))
            print("--- GL Transactions ---")
            for row in result.fetchall():
                print(f"{row[0]} | {row[1]} | {row[2]}")

if __name__ == "__main__":
    asyncio.run(check_costs())
