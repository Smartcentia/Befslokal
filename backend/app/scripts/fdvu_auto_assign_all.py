"""
Auto-assign FDVU requirements for all properties that don't have them yet.
Run: railway run --service BEFS1 python3 backend/app/scripts/fdvu_auto_assign_all.py
"""
import asyncio, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db.session import SessionLocal
from sqlalchemy import text

async def run():
    async with SessionLocal() as db:
        # Finn alle eiendommer
        props = (await db.execute(text("SELECT property_id, name FROM properties ORDER BY name"))).fetchall()
        print(f"Totalt {len(props)} eiendommer")

        # Finn alle krav (requirements)
        reqs = (await db.execute(text("SELECT requirement_id FROM fdv_requirements"))).fetchall()
        req_ids = [r[0] for r in reqs]
        print(f"Totalt {len(req_ids)} krav")

        if not req_ids:
            print("Ingen krav funnet – kjør NS3451/FDVU krav-import først")
            return

        inserted = 0
        skipped = 0

        for prop in props:
            pid = prop[0]
            # Finn eksisterende assignments for denne eiendommen
            existing = (await db.execute(
                text("SELECT requirement_id FROM requirement_assignments WHERE property_id = :pid"),
                {"pid": pid}
            )).fetchall()
            existing_req_ids = {str(r[0]) for r in existing}

            for req_id in req_ids:
                if str(req_id) in existing_req_ids:
                    skipped += 1
                    continue
                await db.execute(text("""
                    INSERT INTO requirement_assignments
                        (assignment_id, property_id, requirement_id, assigned_by, assigned_at)
                    VALUES
                        (gen_random_uuid(), :pid, :rid, 'system_auto', now())
                    ON CONFLICT DO NOTHING
                """), {"pid": pid, "rid": req_id})
                inserted += 1

            if inserted % 500 == 0 and inserted > 0:
                await db.commit()
                print(f"  {inserted} assignments lagt til…")

        await db.commit()
        print(f"\nFerdig: {inserted} nye assignments, {skipped} eksisterende")

        # Tell opp
        total = (await db.execute(text("SELECT COUNT(*) FROM requirement_assignments"))).scalar()
        props_count = (await db.execute(text("SELECT COUNT(DISTINCT property_id) FROM requirement_assignments"))).scalar()
        print(f"Totalt: {total} assignments på {props_count} eiendommer")

if __name__ == "__main__":
    asyncio.run(run())
