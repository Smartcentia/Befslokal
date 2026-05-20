"""
Seed internal control cases for all properties.
Uses InternalControlService.create_initial_cases_for_property.
Skips properties that already have cases (from templates).
"""
import asyncio
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.domains.core.models.property import Property
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.hms.services.internal_control_service import InternalControlService


async def seed_internal_control(dry_run: bool = False):
    """Create initial internal control cases for properties that don't have any."""
    print("Seeding Internal Control cases...")
    if dry_run:
        print("(DRY RUN - no changes will be made)")

    async with SessionLocal() as db:
        # Get all properties
        result = await db.execute(select(Property))
        properties = result.scalars().all()

        if not properties:
            print("No properties found. Run seed_data first.")
            return

        # Count existing cases per property
        count_result = await db.execute(
            select(InternalControlCase.property_id, func.count(InternalControlCase.case_id).label("cnt"))
            .group_by(InternalControlCase.property_id)
        )
        cases_per_property = {str(row[0]): row[1] for row in count_result.fetchall()}

        created_total = 0
        skipped_total = 0

        for prop in properties:
            pid = str(prop.property_id)
            existing = cases_per_property.get(pid, 0)

            if existing > 0:
                if dry_run:
                    print(f"  Would skip {prop.address} (already has {existing} cases)")
                skipped_total += 1
                continue

            if dry_run:
                print(f"  Would create cases for {prop.address}")
                created_total += 1
                continue

            try:
                cases = await InternalControlService.create_initial_cases_for_property(
                    db, prop.property_id, assigned_user_id=None
                )
                created_total += 1
                print(f"  Created {len(cases)} cases for {prop.address}")
            except Exception as e:
                print(f"  ERROR for {prop.address}: {e}")

        if dry_run:
            print(f"\nDry run complete. Would create cases for {created_total} properties, skip {skipped_total}.")
        else:
            print(f"\nDone. Created cases for {created_total} properties, skipped {skipped_total} (already had cases).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed internal control cases for properties")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()

    asyncio.run(seed_internal_control(dry_run=args.dry_run))
