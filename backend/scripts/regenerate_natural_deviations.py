"""
Regenerate natural deviations (internal control cases) after synthetic data cleanup.

This script:
1) Verifies that synthetic properties/cases are gone (or reports how many remain)
2) Generates actionable, "natural" deviations that can be followed:
   - Missing coordinates on properties
   - Overdue scheduled activities
   - Missing risk assessments

Features:
- Dry-run mode (default) to preview changes
- De-duplication: avoids creating duplicate open cases with same title per property

Usage:
  python3 backend/scripts/regenerate_natural_deviations.py --dry-run
  python3 backend/scripts/regenerate_natural_deviations.py --apply

"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

sys.path.insert(0, '/Users/frank/Documents/BEFS_CLEAN/backend')

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
# Ensure all models and relationships are registered before use
import app.db.base  # noqa: F401
from app.domains.core.models.property import Property
from app.domains.hms.models.internal_control import InternalControlCase
from app.domains.hms.models.scheduled_activity import ScheduledActivity
from app.domains.hms.models.risk import RiskAssessment


async def count_synthetic_properties(db: AsyncSession) -> int:
    """Count properties flagged as synthetic via external_data.is_synthetic."""
    query = text(
        """
        SELECT COUNT(*) AS cnt
        FROM properties
        WHERE external_data::text LIKE '%is_synthetic%true%'
        """
    )
    res = await db.execute(query)
    row = res.first()
    return int(row.cnt) if row and hasattr(row, 'cnt') else 0


async def synthetic_cases_exist(db: AsyncSession) -> int:
    """Count cases attached to synthetic properties (for verification)."""
    query = text(
        """
        SELECT COUNT(*) AS cnt
        FROM internal_control_cases c
        WHERE c.property_id IN (
            SELECT p.property_id
            FROM properties p
            WHERE p.external_data::text LIKE '%is_synthetic%true%'
        )
        """
    )
    res = await db.execute(query)
    row = res.first()
    return int(row.cnt) if row and hasattr(row, 'cnt') else 0


async def list_properties_missing_coords(db: AsyncSession) -> List[Property]:
    stmt = select(Property).where(
        (Property.latitude == None) | (Property.longitude == None)
    )
    res = await db.execute(stmt)
    return res.scalars().all()


async def list_overdue_activities(db: AsyncSession) -> List[ScheduledActivity]:
    now = datetime.now(timezone.utc)
    stmt = select(ScheduledActivity).where(
        (ScheduledActivity.enabled.is_(True)) &
        (ScheduledActivity.next_due_date < now)
    )
    res = await db.execute(stmt)
    return res.scalars().all()


async def list_properties_missing_risk_assessment(db: AsyncSession) -> List[str]:
    """Return property_ids that have no risk assessments."""
    # Left-join style query using NOT EXISTS for performance
    query = text(
        """
        SELECT p.property_id
        FROM properties p
        WHERE NOT EXISTS (
            SELECT 1 FROM risk_assessments r
            WHERE r.property_id = p.property_id
        )
        """
    )
    res = await db.execute(query)
    return [str(row.property_id) for row in res.fetchall()]


async def case_exists(db: AsyncSession, property_id: str, title: str) -> bool:
    stmt = select(func.count(InternalControlCase.case_id)).where(
        (InternalControlCase.property_id == property_id) &
        (func.lower(InternalControlCase.status) != 'closed') &
        (func.lower(InternalControlCase.title) == func.lower(title))
    )
    res = await db.execute(stmt)
    cnt = res.scalar_one() or 0
    return cnt > 0


async def create_case(
    db: AsyncSession,
    property_id: str,
    title: str,
    description: Optional[str],
    priority: str,
    due_in_days: int,
    case_type: str = "monthly",
) -> Tuple[bool, Optional[str]]:
    """Create an internal control case if not already present.

    Returns (created, case_id).
    """
    if await case_exists(db, property_id, title):
        return False, None

    due_date = datetime.now(timezone.utc) + timedelta(days=due_in_days)
    new_case = InternalControlCase(
        property_id=property_id,
        title=title,
        description=description or "",
        case_type=case_type,
        status="open",
        priority=priority,
        due_date=due_date,
        notes=None,
        process_state="Opprettet",
        process_data={},
        process_history=[],
    )

    db.add(new_case)
    await db.flush()  # Obtain case_id
    return True, str(new_case.case_id)


async def regenerate_natural_deviations(dry_run: bool = True) -> None:
    async with SessionLocal() as db:
        # 1) Verify synthetic cleanup state
        synth_props = await count_synthetic_properties(db)
        synth_cases = await synthetic_cases_exist(db)
        print(f"Synthetic properties remaining: {synth_props}")
        print(f"Synthetic cases remaining: {synth_cases}")

        # 2) Build list of actionable deviations
        created_count = 0
        created_ids: List[str] = []

        # Missing coordinates
        props_missing_coords = await list_properties_missing_coords(db)
        print(f"Properties missing coordinates: {len(props_missing_coords)}")
        for p in props_missing_coords:
            title = "Manglende koordinater"
            desc = "Eiendommen mangler geodata (lat/lon/geom). Geokoder og oppdater."
            created, case_id = await create_case(
                db,
                property_id=str(p.property_id),
                title=title,
                description=desc,
                priority="medium",
                due_in_days=14,
                case_type="monthly",
            )
            if created:
                created_count += 1
                if case_id:
                    created_ids.append(case_id)

        # Overdue scheduled activities
        overdue = await list_overdue_activities(db)
        print(f"Overdue scheduled activities: {len(overdue)}")
        for a in overdue:
            title = f"Forfalt aktivitet: {a.title}"
            desc = "Planlegg oppfølging og gjennomfør aktiviteten."
            created, case_id = await create_case(
                db,
                property_id=str(a.property_id),
                title=title,
                description=desc,
                priority="high",
                due_in_days=7,
                case_type=a.activity_type if a.activity_type else "monthly",
            )
            if created:
                created_count += 1
                if case_id:
                    created_ids.append(case_id)

        # Missing risk assessments
        props_missing_ra = await list_properties_missing_risk_assessment(db)
        print(f"Properties missing risk assessment: {len(props_missing_ra)}")
        for pid in props_missing_ra:
            title = "Manglende risikovurdering"
            desc = "Eiendommen mangler registrert risikovurdering. Opprett og gjennomfør."
            created, case_id = await create_case(
                db,
                property_id=pid,
                title=title,
                description=desc,
                priority="medium",
                due_in_days=30,
                case_type="annual",
            )
            if created:
                created_count += 1
                if case_id:
                    created_ids.append(case_id)

        # 3) Commit or rollback
        if dry_run:
            await db.rollback()
            print(f"Dry-run: planned to create {created_count} natural deviations. No changes committed.")
        else:
            await db.commit()
            print(f"Created {created_count} natural deviations. Case IDs: {created_ids[:10]}{'...' if len(created_ids) > 10 else ''}")


async def main():
    import argparse
    parser = argparse.ArgumentParser("Regenerate natural deviations")
    parser.add_argument("--dry-run", action="store_true", help="Preview without committing changes")
    parser.add_argument("--apply", action="store_true", help="Apply changes (commit to DB)")
    args = parser.parse_args()

    dry_run = True
    if args.apply:
        dry_run = False
    # default dry-run if neither specified

    try:
        await regenerate_natural_deviations(dry_run=dry_run)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
