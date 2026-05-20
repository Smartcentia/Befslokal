import asyncio
from sqlalchemy import text
from app.db.session import engine

async def migrate():
    async with engine.begin() as conn:
        print("Migrating QA columns...")
        
        # 1. Create Enum Type (if not exists)
        try:
            # Postgres doesn't support IF NOT EXISTS for TYPE easily in one line without block
            # But we can try creation and ignore 'duplicate object' error
            await conn.execute(text("CREATE TYPE qastatus AS ENUM ('pending', 'pass', 'fail');"))
            print("Created Type qastatus")
        except Exception as e:
            print(f"Type qastatus creation skipped (likely exists): {str(e).splitlines()[0]}")
            
        # 2. Add Columns
        try:
            await conn.execute(text("ALTER TABLE ai_tools ADD COLUMN qa_status qastatus DEFAULT 'pending';"))
            print("Added qa_status")
        except Exception as e:
            print(f"Column qa_status skipped: {str(e).splitlines()[0]}")
            
        try:
            await conn.execute(text("ALTER TABLE ai_tools ADD COLUMN qa_report text;"))
            print("Added qa_report")
        except Exception as e:
            print(f"Column qa_report skipped: {str(e).splitlines()[0]}")
            
    print("Migration Complete.")

if __name__ == "__main__":
    asyncio.run(migrate())
