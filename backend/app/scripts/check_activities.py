"""Check activity tables."""
import asyncio, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))
from app.db.session import SessionLocal
from sqlalchemy import text

async def run():
    async with SessionLocal() as db:
        sa = (await db.execute(text("SELECT COUNT(*) FROM scheduled_activities"))).scalar()
        at = (await db.execute(text("SELECT COUNT(*) FROM activity_templates"))).scalar()
        print(f"scheduled_activities: {sa}")
        print(f"activity_templates: {at}")
        # Check a few properties for tags
        rows = (await db.execute(text(
            "SELECT name, external_data->>'tags' FROM properties LIMIT 5"
        ))).fetchall()
        for r in rows:
            print(f"  {r[0]}: tags={r[1]}")

if __name__ == "__main__":
    asyncio.run(run())
