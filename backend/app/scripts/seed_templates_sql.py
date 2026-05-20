"""
Seed activity_templates via raw SQL (bypasser SQLAlchemy ORM import-problemer).
Kjør: railway run --service BEFS1 python3 backend/app/scripts/seed_templates_sql.py
"""
import asyncio, sys, os, json, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db.session import SessionLocal
from sqlalchemy import text

TEMPLATES = [
    # Institusjon / brann
    {"title": "Sjekk brannsentral", "description": "Daglig visuell kontroll av brannsentral for feil og alarmer", "category": "brann", "priority": "high", "activity_type": "daily", "recurrence_pattern": {"frequency": "daily", "interval": 1}, "responsible_role": "vaktmester", "property_tags_required": ["Institusjon"]},
    {"title": "Sjekk rømningsveier", "description": "Kontroller at alle rømningsveier er frie for hindringer", "category": "brann", "priority": "critical", "activity_type": "daily", "recurrence_pattern": {"frequency": "daily", "interval": 1}, "responsible_role": "vaktmester", "property_tags_required": ["Institusjon"]},
    {"title": "Test nødåpner på dører", "description": "Test at alle dører med nødåpnere åpnes automatisk ved brannalarm", "category": "sikkerhet", "priority": "critical", "activity_type": "monthly", "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 1}, "responsible_role": "vaktmester", "property_tags_required": ["RKL6"]},
    {"title": "Kontroll av sikkerhetsglass", "description": "Inspeksjon av vinduer og glassfelt for skader", "category": "sikkerhet", "priority": "high", "activity_type": "quarterly", "recurrence_pattern": {"frequency": "monthly", "interval": 3, "day_of_month": 15}, "responsible_role": "eiendomsansvarlig", "property_tags_required": ["Institusjon"]},
    # Inneklima / ventilasjon
    {"title": "Ventilasjonskontroll", "description": "Sjekk ventiler i fellesarealer, rengjør synlige ventiler", "category": "inneklima", "priority": "medium", "activity_type": "weekly", "recurrence_pattern": {"frequency": "weekly", "interval": 1, "day_of_week": 1}, "responsible_role": "vaktmester", "property_tags_required": None},
    # Brannvern
    {"title": "Kontroll av håndslukkere", "description": "Månedlig egenkontroll: tilstedeværelse, trykk, plombering", "category": "brann", "priority": "high", "activity_type": "monthly", "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 5}, "responsible_role": "vaktmester", "property_tags_required": None},
    {"title": "Kontroll av nødlys", "description": "Visuell sjekk at alle nødlysarmaturer lyser (grønn LED)", "category": "brann", "priority": "medium", "activity_type": "monthly", "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 10}, "responsible_role": "vaktmester", "property_tags_required": None},
    # Leid eiendom
    {"title": "Temperatur- og luftkvalitetslogging", "description": "Dokumenter inneklima for grensesnitt mot utleier", "category": "inneklima", "priority": "medium", "activity_type": "monthly", "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 20}, "responsible_role": "eiendomsansvarlig", "property_tags_required": ["Leid"]},
    {"title": "Grensesnittmøte med utleier", "description": "Gjennomgang av avvik og vedlikeholdsstatus med gårdeier", "category": "hms", "priority": "medium", "activity_type": "quarterly", "recurrence_pattern": {"frequency": "monthly", "interval": 3, "day_of_month": 1}, "responsible_role": "områdeleder", "property_tags_required": ["Leid"]},
    # Generelle HMS
    {"title": "HMS-runde", "description": "Systematisk gjennomgang av HMS-tilstand på hele eiendommen", "category": "hms", "priority": "high", "activity_type": "quarterly", "recurrence_pattern": {"frequency": "monthly", "interval": 3, "day_of_month": 5}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    {"title": "Vedlikeholdsrunde", "description": "Gjennomgang av bygningstekniske forhold – rapport til driftsansvarlig", "category": "teknisk", "priority": "medium", "activity_type": "quarterly", "recurrence_pattern": {"frequency": "monthly", "interval": 3, "day_of_month": 10}, "responsible_role": "vaktmester", "property_tags_required": None},
    {"title": "Energioppfølging", "description": "Les av energimåler og sammenlign med budsjett og forrige periode", "category": "inneklima", "priority": "low", "activity_type": "monthly", "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 1}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    # Årsoppgaver
    {"title": "Brannøvelse", "description": "Gjennomfør obligatorisk brannøvelse med alle beboere og ansatte", "category": "brann", "priority": "critical", "activity_type": "annual", "recurrence_pattern": {"frequency": "yearly", "interval": 1, "month": 3, "day_of_month": 15}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    {"title": "Service av brannvernanlegg", "description": "Avtalt service og kontroll av automatisk brannalarmanlegg", "category": "brann", "priority": "critical", "activity_type": "annual", "recurrence_pattern": {"frequency": "yearly", "interval": 1, "month": 2, "day_of_month": 1}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    {"title": "Elektrisk periodisk kontroll (EPK)", "description": "5-årig lovpålagt el-kontroll av byggets installasjoner", "category": "teknisk", "priority": "critical", "activity_type": "annual", "recurrence_pattern": {"frequency": "yearly", "interval": 5, "month": 1, "day_of_month": 1}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    {"title": "Termografering av elektriske anlegg", "description": "Infrarød-scanning for å avdekke varmgang i el-tavler", "category": "teknisk", "priority": "high", "activity_type": "annual", "recurrence_pattern": {"frequency": "yearly", "interval": 1, "month": 11, "day_of_month": 1}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    # Ukentlige kontroller
    {"title": "Rengjøring av fellesarealer", "description": "Kontroll og rengjøring av korridorer, trapperom og fellesrom", "category": "renhold", "priority": "medium", "activity_type": "weekly", "recurrence_pattern": {"frequency": "weekly", "interval": 1, "day_of_week": 5}, "responsible_role": "vaktmester", "property_tags_required": None},
    {"title": "Utvendig arealinspeksjon", "description": "Visuell kontroll av uteområde, parkering, adkomst og søppelhåndtering", "category": "utvendig", "priority": "low", "activity_type": "weekly", "recurrence_pattern": {"frequency": "weekly", "interval": 1, "day_of_week": 1}, "responsible_role": "vaktmester", "property_tags_required": None},
    {"title": "Heislogg og funksjonskontroll", "description": "Sjekk heislogg for feil, test nødstopp og alarmtelefon", "category": "teknisk", "priority": "high", "activity_type": "weekly", "recurrence_pattern": {"frequency": "weekly", "interval": 1, "day_of_week": 3}, "responsible_role": "vaktmester", "property_tags_required": ["Institusjon"]},
    # Månedlige kontroller
    {"title": "Test sprinkleranlegg", "description": "Funksjonskontroll av sprinklerventiler og trykkmålere", "category": "brann", "priority": "critical", "activity_type": "monthly", "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 15}, "responsible_role": "eiendomsansvarlig", "property_tags_required": ["Institusjon"]},
    {"title": "Kontroll av låssystemer og adgangskontroll", "description": "Test kortlesere, koder og mekaniske låser. Sjekk logg for uautoriserte forsøk", "category": "sikkerhet", "priority": "high", "activity_type": "monthly", "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 8}, "responsible_role": "vaktmester", "property_tags_required": None},
    {"title": "Sjekk varmtvannsbereder (legionella)", "description": "Mål temperatur på varmtvann (min 60°C). Dokumenter avvik for legionellarisiko", "category": "hms", "priority": "critical", "activity_type": "monthly", "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 1}, "responsible_role": "vaktmester", "property_tags_required": None},
    {"title": "Avfallshåndtering og HMS-stasjon", "description": "Gjennomgang av kildesortering, farlig avfall og HMS-datasoner", "category": "hms", "priority": "medium", "activity_type": "monthly", "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 25}, "responsible_role": "vaktmester", "property_tags_required": None},
    {"title": "Kontroll av nødstrømsaggregat", "description": "Test av nødstrømsaggregat – automatisk start, drivstoffnivå og lastkapasitet", "category": "teknisk", "priority": "high", "activity_type": "monthly", "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 20}, "responsible_role": "eiendomsansvarlig", "property_tags_required": ["Institusjon"]},
    {"title": "Fuktighetsmåling kjeller og tekniske rom", "description": "Mål relativ luftfuktighet i kjeller og tekniske rom – dokumenter mot grenseverdier", "category": "inneklima", "priority": "medium", "activity_type": "monthly", "recurrence_pattern": {"frequency": "monthly", "interval": 1, "day_of_month": 12}, "responsible_role": "vaktmester", "property_tags_required": None},
    # Kvartalsvise
    {"title": "Service av ventilasjonsanlegg (filter)", "description": "Bytt eller rengjør filtre i ventilasjonssystemet. Dokumenter filterkvalitet og trykktap", "category": "inneklima", "priority": "high", "activity_type": "quarterly", "recurrence_pattern": {"frequency": "monthly", "interval": 3, "day_of_month": 1}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    {"title": "Kontroll av takrenner og nedløp", "description": "Rens takrenner for løv og debris. Sjekk nedløp og avrenning ved bygget", "category": "utvendig", "priority": "medium", "activity_type": "quarterly", "recurrence_pattern": {"frequency": "monthly", "interval": 3, "day_of_month": 15}, "responsible_role": "vaktmester", "property_tags_required": None},
    {"title": "Brannverndokumentasjon og avviksgjennomgang", "description": "Gjennomgang av brannperm: ROS-analyse, branntegninger, evakueringsplan og logg", "category": "brann", "priority": "high", "activity_type": "quarterly", "recurrence_pattern": {"frequency": "monthly", "interval": 3, "day_of_month": 5}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    {"title": "Periodisk kontroll av bærekonstruksjoner", "description": "Visuell inspeksjon av bjelker, søyler og fundamenter for setningsskader eller sprekker", "category": "teknisk", "priority": "high", "activity_type": "quarterly", "recurrence_pattern": {"frequency": "monthly", "interval": 3, "day_of_month": 20}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    # Halvårlig
    {"title": "Kontroll av løfteutstyr og stiger", "description": "Sjekk arbeidsstiger, trillebord og eventuelt personløftere mot gjeldende krav", "category": "hms", "priority": "medium", "activity_type": "biannual", "recurrence_pattern": {"frequency": "monthly", "interval": 6, "day_of_month": 1}, "responsible_role": "vaktmester", "property_tags_required": None},
    {"title": "Service av varmepumpe / kjøleanlegg", "description": "Rengjøring av fordamper og kondensator, sjekk kjølemiddelnivå og lekkasje", "category": "teknisk", "priority": "medium", "activity_type": "biannual", "recurrence_pattern": {"frequency": "monthly", "interval": 6, "day_of_month": 1}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    # Årsoppgaver tillegg
    {"title": "Overflatebehandling og maling (eksteriør)", "description": "Vurder tilstand på utvendig maling, puss og overflater. Planlegg nødvendig behandling", "category": "utvendig", "priority": "medium", "activity_type": "annual", "recurrence_pattern": {"frequency": "yearly", "interval": 1, "month": 5, "day_of_month": 1}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    {"title": "Revisjon av internkontrollsystem (IK-bygg)", "description": "Gjennomgang og oppdatering av internkontrollsystemet for bygget iht. IK-forskriften", "category": "hms", "priority": "critical", "activity_type": "annual", "recurrence_pattern": {"frequency": "yearly", "interval": 1, "month": 1, "day_of_month": 15}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    {"title": "Universell utforming – årsgjennomgang", "description": "Sjekk at ramper, heiser, HC-parkering og taktile ledelinjer er i orden iht. diskriminerloven", "category": "sikkerhet", "priority": "medium", "activity_type": "annual", "recurrence_pattern": {"frequency": "yearly", "interval": 1, "month": 4, "day_of_month": 1}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    {"title": "Forsikringsgjennomgang og verdivurdering", "description": "Sammenlign bygningsverdi mot forsikringssum. Oppdater forsikringsdokumentasjon", "category": "admin", "priority": "medium", "activity_type": "annual", "recurrence_pattern": {"frequency": "yearly", "interval": 1, "month": 12, "day_of_month": 1}, "responsible_role": "eiendomsansvarlig", "property_tags_required": None},
    {"title": "Snørydding og vintervedlikehold (plan)", "description": "Inngå/forny snøryddingsavtale, sjekk strøsand og issmeltingsmidler er på plass", "category": "utvendig", "priority": "medium", "activity_type": "annual", "recurrence_pattern": {"frequency": "yearly", "interval": 1, "month": 10, "day_of_month": 1}, "responsible_role": "vaktmester", "property_tags_required": None},
    # Leid eiendom tillegg
    {"title": "Arealgjennomgang og leietakertilpasning", "description": "Kartlegg arealutnyttelse og identifiser behov for tilpasning eller ombygning", "category": "teknisk", "priority": "medium", "activity_type": "annual", "recurrence_pattern": {"frequency": "yearly", "interval": 1, "month": 9, "day_of_month": 1}, "responsible_role": "eiendomsansvarlig", "property_tags_required": ["Leid"]},
    {"title": "Regnskap og kostnadsoppfølging (leie)", "description": "Avstem husleiefakturaer mot kontrakt, sjekk KPI-justering og felleskostnader", "category": "admin", "priority": "high", "activity_type": "quarterly", "recurrence_pattern": {"frequency": "monthly", "interval": 3, "day_of_month": 5}, "responsible_role": "eiendomsansvarlig", "property_tags_required": ["Leid"]},
]

async def run():
    async with SessionLocal() as db:
        existing = (await db.execute(text("SELECT COUNT(*) FROM activity_templates"))).scalar()
        print(f"Eksisterende templates: {existing}")

        if existing and existing > 0:
            print("Templates finnes allerede – sletter og re-seeder")
            await db.execute(text("DELETE FROM activity_templates WHERE scope = 'system' OR scope IS NULL"))
            await db.commit()

        for t in TEMPLATES:
            rpat = json.dumps(t["recurrence_pattern"])
            tags_req = json.dumps(t.get("property_tags_required")) if t.get("property_tags_required") else None
            # Use cast in Python, pass plain text to DB
            await db.execute(text(
                "INSERT INTO activity_templates "
                "(template_id, title, description, category, priority, activity_type, "
                "recurrence_pattern, responsible_role, property_tags_required, "
                "property_tags_excluded, enabled, version) "
                "VALUES (:tid, :title, :desc, :cat, :prio, :atype, "
                "cast(:rpat AS jsonb), :role, cast(:tags_req AS jsonb), "
                "NULL, true, 1)"
            ), {
                "tid": str(uuid.uuid4()),
                "title": t["title"],
                "desc": t.get("description"),
                "cat": t["category"],
                "prio": t["priority"],
                "atype": t["activity_type"],
                "rpat": rpat,
                "role": t["responsible_role"],
                "tags_req": tags_req,
            })

        await db.commit()
        count = (await db.execute(text("SELECT COUNT(*) FROM activity_templates"))).scalar()
        print(f"Seeded → {count} templates i DB")

if __name__ == "__main__":
    asyncio.run(run())
