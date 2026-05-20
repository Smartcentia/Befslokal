"""
Quick script to seed test users in production database
Reads from .env and executes seed_simple_users.sql
"""
import asyncio
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def seed_users():
    # Load DATABASE_URL from .env
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    os.environ["DATABASE_URL"] = line.split("=", 1)[1].strip('"').strip("'")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment!")
        return
    
    # Read SQL file
    sql_path = Path(__file__).parent / "seed_simple_users.sql"
    if not sql_path.exists():
        print(f"❌ SQL file not found: {sql_path}")
        return
    
    sql_content = sql_path.read_text()
    
    print(f"📋 Connecting to database...")
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            print(f"✅ Connected! Executing seed script...")
            await conn.execute(text(sql_content))
            print(f"✅ Seed script executed successfully!")
            
            # Verify
            result = await conn.execute(text("""
                SELECT role, COUNT(*) as count
                FROM users
                GROUP BY role
                ORDER BY 
                    CASE role
                        WHEN 'ADMIN' THEN 1
                        WHEN 'REGIONAL_MANAGER' THEN 2
                        WHEN 'PROPERTY_MANAGER' THEN 3
                    END
            """))
            rows = result.fetchall()
            
            print("\n📊 User Summary:")
            for row in rows:
                print(f"  {row[0]}: {row[1]} users")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_users())
