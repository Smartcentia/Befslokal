# Cron-jobs for internkontroll

For å kjøre automatisk oppfølging og aktivitetsprosessering, konfigurer følgende cron-jobs.

## Endepunkter

| Jobb | Endepunkt | Rolle | Beskrivelse |
|------|-----------|-------|-------------|
| Process due activities | `POST /api/v1/hms/activities/process-due` | ADMIN | Oppretter InternalControlCase for forfalte ScheduledActivity |
| Oppfølging forfalte | `POST /api/v1/internal-control/process-overdue` | ADMIN | Sender purringer og eskalerer forfalte internkontroll-saker |
| Batch risk update | `POST /api/v1/risk/batch-update` | ADMIN | Oppdaterer risikovurderinger (valgfritt, ukentlig) |

## Railway Cron Job

I Railway Dashboard: **New** → **Cron Job** (eller opprett Worker service)

1. **Process due activities** (daglig 06:00)
   - Schedule: `0 6 * * *` (hver dag kl 06:00 UTC)
   - Build: `pip install -r backend/requirements.txt` (eller bruk samme image som backend)
   - Command: `curl -X POST -H "Authorization: Bearer $CRON_SECRET" https://<backend-url>/api/v1/hms/activities/process-due`

2. **Oppfølging forfalte** (daglig 08:00)
   - Schedule: `0 8 * * *`
   - Command: `curl -X POST -H "Authorization: Bearer $CRON_SECRET" https://<backend-url>/api/v1/internal-control/process-overdue`

**Merk:** Backend må støtte CRON_SECRET for uautentisert cron. Alternativt: Kjør et Python-script som bruker intern DB-tilkobling og kaller servicene direkte.

## Alternativ: Python-script

Opprett `backend/scripts/run_cron_jobs.py` som kjører begge jobbene:

```python
import asyncio
from app.db.session import SessionLocal
from app.domains.hms.services.activity_scheduler import ActivityScheduler
from app.domains.hms.services.follow_up_service import FollowUpService

async def main():
    async with SessionLocal() as db:
        scheduler = ActivityScheduler()
        await scheduler.process_due_activities(db)
        await FollowUpService.process_overdue_cases(db)

if __name__ == "__main__":
    asyncio.run(main())
```

Cron: `cd backend && python scripts/run_cron_jobs.py`
