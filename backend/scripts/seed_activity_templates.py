"""
Seed activity_templates from ActivityGenerator.DEFAULT_TEMPLATES.
Kjør for å fylle hub med system-maler.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from app.db.session import SessionLocal
from app.domains.hms.models.scheduled_activity import ActivityTemplate
from app.domains.hms.services.activity_generator import ActivityGenerator


async def seed_activity_templates():
    print("Seeding activity templates...")
    async with SessionLocal() as db:
        result = await db.execute(select(ActivityTemplate))
        existing = result.scalars().all()
        if existing:
            print(f"Found {len(existing)} existing templates. Skipping (delete first to re-seed).")
            return

        for t in ActivityGenerator.DEFAULT_TEMPLATES:
            template = ActivityTemplate(
                title=t["title"],
                description=t.get("description"),
                category=t["category"],
                priority=t["priority"],
                activity_type=t["activity_type"],
                recurrence_pattern=t["recurrence_pattern"],
                responsible_role=t["responsible_role"],
                property_tags_required=t.get("property_tags_required"),
                property_tags_excluded=t.get("property_tags_excluded"),
                enabled=True,
                scope="system",
            )
            db.add(template)

        await db.commit()
        print(f"Seeded {len(ActivityGenerator.DEFAULT_TEMPLATES)} activity templates.")


if __name__ == "__main__":
    asyncio.run(seed_activity_templates())
