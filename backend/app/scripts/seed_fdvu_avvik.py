"""
Seeder FDVU-relaterte avvik og varsler for alle eiendommer.

Lager realistiske internkontroll-saker basert på FDVU-oppfølging:
  - Brannsikkerhet, ventilasjon, el-kontroll, HMS, vedlikehold etc.
  - Ulike varianter, prioriteter og statuser per eiendom
  - Varsler til relevante FDVU- og driftsansvarlige

Kjøring:
    cd backend
    python -m app.scripts.seed_fdvu_avvik
"""
import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid4

import app.db.base  # noqa: F401
from sqlalchemy import select, text
from app.db.session import SessionLocal
from app.domains.hms.models.internal_control import InternalControlCase, Notification
from app.domains.core.models.property import Property
from app.domains.core.models.user import User, UserRole

random.seed(42)

# ── FDVU-avviksmaler ─────────────────────────────────────────────────────────

FDVU_AVVIK = [
    # Brannsikkerhet
    {
        "title": "Manglende branntilsyn",
        "description": "Periodisk branntilsyn er ikke gjennomført innen fristen. Brannteknisk dokumentasjon mangler for inneværende år.",
        "case_type": "annual",
        "priority": "critical",
        "days_overdue": (-90, -1),   # overdue
        "status_pool": ["open", "open", "in_progress"],
    },
    {
        "title": "Brannslukningsapparat mangler service",
        "description": "Ett eller flere brannslukningsapparater har ikke fått godkjent årsservice. Servicerapport ikke mottatt.",
        "case_type": "annual",
        "priority": "high",
        "days_overdue": (-60, 30),
        "status_pool": ["open", "open", "in_progress"],
    },
    {
        "title": "Rømningsveier ikke kontrollert",
        "description": "Rømningsveier er ikke kontrollert og dokumentert. Dører og nødlys mangler kvartalssjekk.",
        "case_type": "quarterly",
        "priority": "high",
        "days_overdue": (-45, 15),
        "status_pool": ["open", "in_progress"],
    },
    # Ventilasjon
    {
        "title": "Ventilasjonsanlegg ikke rengjort",
        "description": "Ventilasjonskanaler og aggregat er ikke rengjort per årsplan. Luftkvalitetsmåling mangler.",
        "case_type": "annual",
        "priority": "medium",
        "days_overdue": (-30, 60),
        "status_pool": ["open", "open", "in_progress", "open"],
    },
    {
        "title": "Manglende ventilasjonskontroll (luftmengdemåling)",
        "description": "Luftmengdemåling er ikke utført. Aggregat viser avvik på temperatur og trykk.",
        "case_type": "annual",
        "priority": "medium",
        "days_overdue": (-20, 90),
        "status_pool": ["open", "in_progress"],
    },
    # El-sikkerhet
    {
        "title": "El-sikkerhetskontroll forfalt",
        "description": "Periodisk el-sikkerhetskontroll (termografering + visuell inspeksjon) er ikke gjennomført. Siste rapport er over 24 måneder gammel.",
        "case_type": "annual",
        "priority": "critical",
        "days_overdue": (-120, -10),
        "status_pool": ["open", "open"],
    },
    {
        "title": "Manglende termografering av el-anlegg",
        "description": "Termografering er ikke bestilt eller gjennomført. Avvik fra siste sjekk er ikke lukket.",
        "case_type": "annual",
        "priority": "high",
        "days_overdue": (-60, 30),
        "status_pool": ["open", "in_progress"],
    },
    # HMS
    {
        "title": "HMS-vernerunde ikke gjennomført",
        "description": "Kvartalsmessig vernerunde er ikke gjennomført. Protokoll og handlingsplan mangler.",
        "case_type": "quarterly",
        "priority": "high",
        "days_overdue": (-30, 20),
        "status_pool": ["open", "open", "in_progress"],
    },
    {
        "title": "Manglende HMS-opplæring av ansatte",
        "description": "Ny ansatt har ikke gjennomført obligatorisk HMS-opplæring. Sertifikat og dokumentasjon mangler.",
        "case_type": "annual",
        "priority": "medium",
        "days_overdue": (-10, 45),
        "status_pool": ["open", "in_progress"],
    },
    {
        "title": "Risikovurdering ikke oppdatert",
        "description": "Risikovurdering for bygningsmassen er ikke revidert siste 12 måneder. Ny kartlegging påkrevd.",
        "case_type": "annual",
        "priority": "medium",
        "days_overdue": (-90, -5),
        "status_pool": ["open", "open"],
    },
    # Vedlikehold
    {
        "title": "Lekkasje i tak ikke utbedret",
        "description": "Lekkasje observert i tak/fasade. Midlertidig tiltak iverksatt, men permanent utbedring mangler. Fuktmåling viser forhøyede verdier.",
        "case_type": "monthly",
        "priority": "critical",
        "days_overdue": (-30, 10),
        "status_pool": ["open", "in_progress", "open"],
    },
    {
        "title": "Vedlikeholdsplan ikke fulgt",
        "description": "Planlagte vedlikeholdsoppgaver fra årsplanen er ikke gjennomført. Budsjett ikke benyttet.",
        "case_type": "quarterly",
        "priority": "medium",
        "days_overdue": (-60, 30),
        "status_pool": ["open", "in_progress"],
    },
    {
        "title": "Manglende serviceavtale for heis",
        "description": "Heisservice er forfalt. Servicerapport mangler. Statsautorisert heiskontroll ikke bestilt.",
        "case_type": "annual",
        "priority": "high",
        "days_overdue": (-45, 30),
        "status_pool": ["open", "open", "in_progress"],
    },
    {
        "title": "Utendørsareal ikke vedlikeholdt",
        "description": "Asfalt, gangveier og uteområder er ikke vedlikeholdt. Fare for snubleulykker. Vinterdrift-avtale utgått.",
        "case_type": "quarterly",
        "priority": "low",
        "days_overdue": (0, 90),
        "status_pool": ["open"],
    },
    # Internkontroll / dokumentasjon
    {
        "title": "Internkontrollsystem ikke oppdatert",
        "description": "IK-systemet er ikke revidert. Prosedyrer, ansvarsmatriser og sjekklister er utdaterte (>12 mnd).",
        "case_type": "annual",
        "priority": "medium",
        "days_overdue": (-90, -1),
        "status_pool": ["open"],
    },
    {
        "title": "Manglende driftslogg",
        "description": "Driftslogg for tekniske anlegg er ikke ført siste måned. Loggbok mangler registreringer.",
        "case_type": "monthly",
        "priority": "low",
        "days_overdue": (-20, 10),
        "status_pool": ["open", "in_progress"],
    },
    {
        "title": "Fuktkartlegging ikke gjennomført",
        "description": "Obligatorisk fuktkartlegging er ikke bestilt. Risiko for skjult fuktskade i kjeller/tak.",
        "case_type": "annual",
        "priority": "high",
        "days_overdue": (-30, 60),
        "status_pool": ["open"],
    },
    {
        "title": "Nødlystest ikke dokumentert",
        "description": "Månedlig test av nødlysanlegg er ikke dokumentert. Testlogg mangler for siste 3 måneder.",
        "case_type": "monthly",
        "priority": "medium",
        "days_overdue": (-30, 5),
        "status_pool": ["open", "in_progress"],
    },
]

# Brukere som mottar varsler (FDVU-roller)
FDVU_USER_IDS = [
    "db3e5db4-6d5a-46fb-ae34-cc5cc3844079",  # FDVU_KOORDINATOR nord
    "673514b3-62f3-442d-8375-53b3f999f58f",  # FDVU_KOORDINATOR øst
    "ee61a610-fd14-408b-9fa7-c94fd12ce7a0",  # FDVU_KOORDINATOR vest
    "e1f13af2-eb35-4c4e-bec4-8cc52520eac7",  # DRIFTSANSVARLIG nord
    "6a467a00-2f58-4592-8c36-a316d38f8049",  # DRIFTSANSVARLIG sør
    "d5d617a4-5be4-49b2-bad6-7822783222b2",  # HMS_ANSVARLIG
    "ce5cd129-f956-4596-b2ee-0095dad93f5b",  # ADMIN (frankvevle)
]


def pick_due_date(days_overdue_range: tuple[int, int]) -> datetime:
    days = random.randint(*days_overdue_range)
    return datetime.utcnow() + timedelta(days=days)


async def seed() -> None:
    async with SessionLocal() as db:
        # Hent alle eiendommer
        result = await db.execute(select(Property))
        properties = result.scalars().all()
        print(f"\n🏢 Fant {len(properties)} eiendommer\n")

        # Sjekk eksisterende FDVU-avvik
        existing = await db.execute(
            text("SELECT COUNT(*) FROM internal_control_cases WHERE case_type IN ('monthly','quarterly','annual') AND title LIKE '%Manglende%' OR title LIKE '%ikke%' OR title LIKE '%forfalt%'")
        )
        existing_count = existing.scalar() or 0

        total_cases = 0
        total_notifs = 0

        for prop in properties:
            prop_id = str(prop.property_id)

            # Velg 3–6 tilfeldige FDVU-avvik per eiendom (ingen duplikater)
            num_avvik = random.randint(3, 6)
            selected = random.sample(FDVU_AVVIK, num_avvik)

            for avvik in selected:
                due = pick_due_date(avvik["days_overdue"])
                status = random.choice(avvik["status_pool"])

                case = InternalControlCase(
                    case_id=uuid4(),
                    property_id=prop_id,
                    title=f"{avvik['title']} — {prop.name or prop.address or 'Ukjent'}",
                    description=avvik["description"],
                    case_type=avvik["case_type"],
                    priority=avvik["priority"],
                    status=status,
                    due_date=due,
                    process_state="Opprettet" if status == "open" else "Under behandling",
                    process_data={"fdvu": True, "kategori": avvik["case_type"]},
                    process_history=[],
                    follow_up_status="none",
                )
                db.add(case)
                total_cases += 1

            await db.flush()

        # Varsler til FDVU-brukere om kritiske og høy-prioritets avvik
        await db.flush()
        critical_cases_res = await db.execute(
            text("""
                SELECT case_id, title, property_id
                FROM internal_control_cases
                WHERE priority IN ('critical','high')
                  AND status = 'open'
                  AND process_data::jsonb->>'fdvu' = 'true'
                ORDER BY RANDOM()
                LIMIT 60
            """)
        )
        critical_cases = critical_cases_res.fetchall()

        for case_row in critical_cases:
            # Send varsel til 1–2 tilfeldige FDVU-brukere
            for user_id in random.sample(FDVU_USER_IDS, k=min(2, len(FDVU_USER_IDS))):
                notif = Notification(
                    notification_id=uuid4(),
                    user_id=user_id,
                    title=f"⚠️ FDVU-avvik: {case_row.title[:60]}",
                    message=(
                        f"Et {('kritisk' if 'Manglende brann' in case_row.title or 'El-sikkerhets' in case_row.title else 'høy-prioritets')} "
                        f"FDVU-avvik krever oppfølging. Gjennomfør kontroll og dokumenter tiltak."
                    ),
                    notification_type="fdvu",
                    related_entity_type="case",
                    related_entity_id=case_row.case_id,
                    is_read=False,
                )
                db.add(notif)
                total_notifs += 1

        await db.commit()

        print(f"✅ Seedet {total_cases} FDVU-avvik for {len(properties)} eiendommer")
        print(f"🔔 Opprettet {total_notifs} varsler til FDVU-brukere")
        print()
        print("   Avvikstyper:")
        for t in FDVU_AVVIK:
            print(f"   [{t['priority'].upper():<8}] {t['case_type']:<12} {t['title']}")
        print()
        print("   Se avvik på: /cases eller i Innboks → Avvik")


if __name__ == "__main__":
    asyncio.run(seed())
