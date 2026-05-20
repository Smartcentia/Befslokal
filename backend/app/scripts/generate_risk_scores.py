"""
Auto-generer RiskAssessment-poster for alle eiendommer basert på:
- Antall og alvorlighet av åpne avvik (InternalControlCase)
- Kontraktsstatus (utløper snart = høyere risiko)
- GL-kostnader (høy kostnadsvekst = risiko)

Kjør: railway run --service BEFS1 python3 backend/app/scripts/generate_risk_scores.py
"""
import sys, os, asyncio, uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.db.session import SessionLocal
from sqlalchemy import text

METHODOLOGY = "auto_befs_2026"

def compute_risk(dev_kritisk, dev_hoy, dev_medium, dev_total,
                 contracts_expiring_soon, days_to_expiry,
                 gl_cost_2025, has_gl_data):
    """Beregn risikoscore 0-100 og kategori."""

    # Avviksscore (max 60 poeng)
    dev_score = min(60, (
        dev_kritisk * 20 +
        dev_hoy * 10 +
        dev_medium * 4 +
        max(0, dev_total - dev_kritisk - dev_hoy - dev_medium) * 2
    ))

    # Kontraktsscore (max 25 poeng)
    contract_score = 0.0
    if contracts_expiring_soon:
        if days_to_expiry is not None and days_to_expiry <= 90:
            contract_score = 25
        elif days_to_expiry is not None and days_to_expiry <= 180:
            contract_score = 15
        elif days_to_expiry is not None and days_to_expiry <= 365:
            contract_score = 8

    # Kostnadsscore (max 15 poeng) — bare en mild indikasjon
    cost_score = 0.0
    if has_gl_data:
        if gl_cost_2025 > 20_000_000:
            cost_score = 15
        elif gl_cost_2025 > 10_000_000:
            cost_score = 10
        elif gl_cost_2025 > 5_000_000:
            cost_score = 5

    total = min(100, dev_score + contract_score + cost_score)

    if total >= 75:
        cat = "Kritisk"
    elif total >= 50:
        cat = "Høy"
    elif total >= 25:
        cat = "Medium"
    else:
        cat = "Lav"

    return round(total, 1), cat


async def run():
    async with SessionLocal() as db:
        # Hent alle eiendommer
        props = (await db.execute(text("SELECT property_id, name FROM properties ORDER BY name"))).fetchall()
        print(f"Fant {len(props)} eiendommer")

        # Avvik per property
        devs = (await db.execute(text("""
            SELECT property_id::text, priority, COUNT(*) cnt
            FROM internal_control_cases
            WHERE status NOT IN ('closed','lukket','Lukket')
            GROUP BY property_id, priority
        """))).fetchall()
        dev_map = {}
        for r in devs:
            pid = str(r[0])
            if pid not in dev_map:
                dev_map[pid] = {}
            dev_map[pid][str(r[1]).lower()] = int(r[2])

        # Kontrakter med utløpsdato (via units → properties)
        contracts = (await db.execute(text("""
            SELECT u.property_id::text, c.end_date
            FROM contracts c
            JOIN units u ON u.unit_id = c.unit_id
            WHERE c.status = 'active' AND c.end_date IS NOT NULL
            ORDER BY c.end_date ASC
        """))).fetchall()
        contract_map = {}
        today = datetime.now(timezone.utc).date()
        for r in contracts:
            pid = str(r[0])
            ed = r[1]
            if ed is None:
                continue
            if hasattr(ed, 'date'):
                ed = ed.date()
            days = (ed - today).days
            if pid not in contract_map or days < contract_map[pid]:
                contract_map[pid] = days

        # GL-kostnader 2025
        gl = (await db.execute(text("""
            SELECT property_id::text, ABS(SUM(belop)) AS total
            FROM gl_transactions
            WHERE ar = 2025 AND property_id IS NOT NULL
            GROUP BY property_id
        """))).fetchall()
        gl_map = {str(r[0]): float(r[1]) for r in gl}

        # Slett eksisterende auto-vurderinger
        await db.execute(text(
            "DELETE FROM risk_assessments WHERE methodology = :m"
        ), {"m": METHODOLOGY})
        await db.commit()
        print("Slettet gamle auto-vurderinger")

        generated = 0
        for prop in props:
            pid = str(prop[0])
            dmap = dev_map.get(pid, {})
            dev_k = dmap.get('kritisk', 0) + dmap.get('critical', 0)
            dev_h = dmap.get('høy', 0) + dmap.get('hoy', 0) + dmap.get('high', 0)
            dev_m = dmap.get('medium', 0)
            dev_total = sum(dmap.values())

            days_exp = contract_map.get(pid)
            has_contract = days_exp is not None

            gl_cost = gl_map.get(pid, 0)
            has_gl = pid in gl_map

            score, cat = compute_risk(
                dev_k, dev_h, dev_m, dev_total,
                has_contract, days_exp,
                gl_cost, has_gl
            )

            assessment_id = str(uuid.uuid4())
            await db.execute(text("""
                INSERT INTO risk_assessments
                    (assessment_id, property_id, assessment_date, methodology,
                     overall_risk_score, risk_category, assessed_by,
                     notes, data_confidence, assessment_status)
                VALUES
                    (:aid, :pid, now(), :meth,
                     :score, :cat, 'system_auto',
                     :notes, :conf, 'OPEN')
            """), {
                "aid": assessment_id,
                "pid": prop[0],
                "meth": METHODOLOGY,
                "score": score,
                "cat": cat,
                "notes": f"Auto-generert: {dev_total} avvik ({dev_k} kritiske), kontraktsdager={days_exp}, GL={gl_cost/1e6:.1f}M",
                "conf": 0.7 if (dev_total > 0 or has_contract or has_gl) else 0.3,
            })
            generated += 1
            if generated % 20 == 0:
                await db.commit()
                print(f"  {generated}/{len(props)} bearbeidet…")

        await db.commit()
        print(f"\nGenererte {generated} risikoscorer")

        # Vis fordeling
        dist = (await db.execute(text("""
            SELECT risk_category, COUNT(*), ROUND(AVG(overall_risk_score)::numeric,1)
            FROM risk_assessments WHERE methodology = :m
            GROUP BY risk_category ORDER BY 3 DESC
        """), {"m": METHODOLOGY})).fetchall()
        print("\nFordeling:")
        for r in dist:
            print(f"  {r[0]}: {r[1]} eiendommer, snitt score {r[2]}")


if __name__ == "__main__":
    asyncio.run(run())
