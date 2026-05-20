"""
Run cron jobs for internkontroll.
Process due activities and overdue case follow-up.
Kjør f.eks. daglig via cron: cd backend && python scripts/run_cron_jobs.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.db.session import SessionLocal
from app.domains.hms.services.activity_scheduler import ActivityScheduler
from app.domains.hms.services.follow_up_service import FollowUpService
from app.services.analytics.ml_watchdog import MLWatchdog


async def main():
    print("Running cron jobs...")
    async with SessionLocal() as db:
        # 1. HMS & Internkontroll
        scheduler = ActivityScheduler()
        stats1 = await scheduler.process_due_activities(db)
        print(f"Process due activities: {stats1}")

        stats2 = await FollowUpService.process_overdue_cases(db)
        print(f"Process overdue cases: {stats2}")

        # 2. ML & Analyse (Ny)
        print("Running ML Watchdog...")
        try:
            anomalies = await MLWatchdog.scan_for_anomalies(db)
            await MLWatchdog.update_pattern_memory(db)
            print(f"ML Watchdog complete. Anomalies detected: {anomalies}")
        except Exception as e:
            print(f"ML Watchdog failed: {e}")

    print("Cron jobs complete.")


if __name__ == "__main__":
    asyncio.run(main())
