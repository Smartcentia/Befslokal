#!/usr/bin/env python3
"""
Check internal control cases in the database using raw SQL to avoid ORM issues.
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal

async def main():
    print("=" * 70)
    print("CHECKING INTERNAL CONTROL CASES")
    print("=" * 70)
    
    async with SessionLocal() as db:
        # Check total count
        result = await db.execute(text("SELECT COUNT(*) FROM internal_control_cases"))
        total_count = result.scalar()
        print(f"\nTotal Internal Control Cases: {total_count}")

        if total_count == 0:
            print("\n⚠️  No cases found in database.")
            return

        # Check by priority
        result = await db.execute(text("""
            SELECT priority, COUNT(*) as count 
            FROM internal_control_cases 
            GROUP BY priority
            ORDER BY count DESC
        """))
        print("\nCases by Priority:")
        for row in result.all():
            print(f"  - {row.priority}: {row.count}")

        # Check by status
        result = await db.execute(text("""
            SELECT status, COUNT(*) as count 
            FROM internal_control_cases 
            GROUP BY status
            ORDER BY count DESC
        """))
        print("\nCases by Status:")
        for row in result.all():
            print(f"  - {row.status}: {row.count}")

        # Specific check for high/critical priority
        result = await db.execute(text("""
            SELECT COUNT(*) 
            FROM internal_control_cases 
            WHERE priority IN ('high', 'critical')
        """))
        high_crit_count = result.scalar()
        print(f"\n📊 High/Critical Priority Cases: {high_crit_count}")
        
        # Sample some high/critical cases
        if high_crit_count > 0:
            result = await db.execute(text("""
                SELECT title, priority, status, due_date
                FROM internal_control_cases 
                WHERE priority IN ('high', 'critical')
                LIMIT 5
            """))
            print("\nSample High/Critical Cases:")
            for row in result.all():
                print(f"  - [{row.priority.upper()}] {row.title} (Status: {row.status}, Due: {row.due_date})")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
