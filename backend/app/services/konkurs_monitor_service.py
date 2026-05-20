"""
Konkurs Monitor Service – nightly check of bankruptcy/risk flags for all active parties.

For each party with orgnr:
  1. Fresh BRREG Enhetsregisteret fetch to get current status flags
  2. Extract: konkurs, underAvvikling, tvangsopplosning, slettet, manglende regnskap
  3. Store in party.external_data['konkurs_status']

Run nightly via APScheduler (see main.py) or manually via:
  POST /api/v1/konkurs-monitor/run-all

Also checks the Konkursregisteret varsel API (data.brreg.no) for new bankruptcy notices.
"""
import logging
import asyncio
from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

_job_lock = asyncio.Lock()

CURRENT_YEAR = date.today().year


def _extract_risk(enhet: dict) -> dict:
    """
    Extract konkurs/risk flags from a fresh BRREG enhet dict.
    Returns a konkurs_status dict.
    """
    risk_flags: list[str] = []
    risk_level = "OK"

    konkurs = bool(enhet.get("konkurs"))
    under_avvikling = bool(enhet.get("underAvvikling"))
    under_tvangsavvikling = bool(enhet.get("underTvangsavviklingEllerTvangsopplosning"))
    slettet = bool(enhet.get("slettedato"))

    # Tvangsoppløsnings-årsaker
    tvangs_styre = enhet.get("tvangsopplostPgaMangelfulltStyreDato")
    tvangs_leder = enhet.get("tvangsopplostPgaManglendeDagligLederDato")
    tvangs_regnskap = enhet.get("tvangsopplostPgaManglendeRegnskapDato")
    tvangs_revisor = enhet.get("tvangsopplostPgaManglendeRevisorDato")
    tvangs_slett = enhet.get("tvangsavvikletPgaManglendeSlettingDato")

    # Siste regnskap
    siste_regnskap = enhet.get("sisteInnsendteAarsregnskap")
    mangler_regnskap = False
    if siste_regnskap and isinstance(siste_regnskap, int):
        if (CURRENT_YEAR - siste_regnskap) >= 2:
            mangler_regnskap = True

    # Risk classification
    if konkurs:
        risk_flags.append(f"Konkurs åpnet{' ' + str(enhet.get('konkursdato')) if enhet.get('konkursdato') else ''}")
        risk_level = "CRITICAL"

    if slettet:
        risk_flags.append(f"Slettet fra Enhetsregisteret ({enhet.get('slettedato')})")
        risk_level = "CRITICAL"

    if under_tvangsavvikling:
        risk_flags.append("Under tvangsavvikling / tvangsoppløsning")
        if risk_level != "CRITICAL":
            risk_level = "CRITICAL"

    if tvangs_styre:
        risk_flags.append(f"Tvangsoppløst: mangelfullt styre ({tvangs_styre})")
        if risk_level != "CRITICAL":
            risk_level = "WARNING"

    if tvangs_leder:
        risk_flags.append(f"Tvangsoppløst: manglende daglig leder ({tvangs_leder})")
        if risk_level != "CRITICAL":
            risk_level = "WARNING"

    if tvangs_regnskap:
        risk_flags.append(f"Tvangsoppløst: manglende regnskap ({tvangs_regnskap})")
        if risk_level != "CRITICAL":
            risk_level = "WARNING"

    if tvangs_revisor:
        risk_flags.append(f"Tvangsoppløst: manglende revisor ({tvangs_revisor})")
        if risk_level != "CRITICAL":
            risk_level = "WARNING"

    if tvangs_slett:
        risk_flags.append(f"Tvangsavviklet: manglende sletting ({tvangs_slett})")
        if risk_level != "CRITICAL":
            risk_level = "WARNING"

    if under_avvikling:
        risk_flags.append(f"Under frivillig avvikling{' siden ' + str(enhet.get('underAvviklingDato')) if enhet.get('underAvviklingDato') else ''}")
        if risk_level == "OK":
            risk_level = "WARNING"

    if mangler_regnskap:
        risk_flags.append(f"Mangler regnskap: siste innsendte var {siste_regnskap}")
        if risk_level == "OK":
            risk_level = "WARNING"

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "konkurs": konkurs,
        "under_avvikling": under_avvikling,
        "under_tvangsavvikling": under_tvangsavvikling,
        "slettet": slettet,
        "mangler_regnskap": mangler_regnskap,
        "siste_regnskap_aar": siste_regnskap,
        "risk_level": risk_level,
        "risk_flags": risk_flags,
    }


async def check_single_party(db: AsyncSession, party_id: str) -> Optional[dict]:
    """
    Run konkurs check for a single party. Returns konkurs_status dict or None.
    """
    from app.domains.core.models.party import Party
    from app.services.external.brreg_service import BrregService
    from sqlalchemy.orm.attributes import flag_modified

    result_q = await db.execute(select(Party).where(Party.party_id == party_id))
    party = result_q.scalar_one_or_none()
    if not party or not party.orgnr:
        return None

    orgnr = party.orgnr.strip()
    if len(orgnr) != 9 or not orgnr.isdigit():
        return None

    try:
        enhet = await BrregService.get_enhet(orgnr)
        if not enhet:
            return None

        status = _extract_risk(enhet)

        # Also update brreg_enhet with fresh data
        ext = dict(party.external_data or {})
        ext["brreg_enhet"] = enhet
        ext["konkurs_status"] = status
        party.external_data = ext
        flag_modified(party, "external_data")
        await db.commit()
        return status
    except Exception as e:
        logger.warning("konkurs_monitor: check_single_party %s failed: %s", party_id, e)
        return None


async def run_all_parties(db: AsyncSession, limit: int = 300) -> dict:
    """
    Run konkurs check for all parties with orgnr.
    Returns summary stats + list of flagged parties.
    """
    if _job_lock.locked():
        logger.info("konkurs_monitor: job already running, skipping")
        return {"status": "already_running"}

    async with _job_lock:
        logger.info("konkurs_monitor: starting nightly check")

        from app.domains.core.models.party import Party
        from app.services.external.brreg_service import BrregService
        from sqlalchemy.orm.attributes import flag_modified
        from sqlalchemy import text

        try:
            result = await db.execute(
                select(Party).where(Party.orgnr.isnot(None)).limit(limit)
            )
            parties = result.scalars().all()
            candidates = [
                p for p in parties
                if p.orgnr and len(p.orgnr.strip()) == 9 and p.orgnr.strip().isdigit()
            ]

            total = len(candidates)
            done = flagged = errors = 0
            flagged_parties: list[dict] = []

            logger.info("konkurs_monitor: checking %d parties", total)

            for i, party in enumerate(candidates):
                try:
                    orgnr = party.orgnr.strip()
                    enhet = await BrregService.get_enhet(orgnr)
                    if enhet:
                        status = _extract_risk(enhet)
                        ext = dict(party.external_data or {})
                        ext["brreg_enhet"] = enhet
                        ext["konkurs_status"] = status
                        party.external_data = ext
                        flag_modified(party, "external_data")

                        if status["risk_level"] in ("CRITICAL", "WARNING"):
                            flagged += 1
                            flagged_parties.append({
                                "party_id": str(party.party_id),
                                "name": party.name,
                                "orgnr": orgnr,
                                "risk_level": status["risk_level"],
                                "risk_flags": status["risk_flags"],
                            })
                    done += 1
                except Exception as e:
                    logger.debug("konkurs_monitor: failed %s: %s", party.orgnr, e)
                    errors += 1

                # Commit every 20, rate-limit every 10
                if (done + errors) % 20 == 0:
                    await db.commit()
                    logger.info("konkurs_monitor: %d/%d done, %d flagged", done, total, flagged)
                if (done + errors) % 10 == 0:
                    await asyncio.sleep(1)

            await db.commit()
            logger.info(
                "konkurs_monitor: finished – done=%d flagged=%d errors=%d",
                done, flagged, errors
            )
            return {
                "status": "ok",
                "total": total,
                "done": done,
                "flagged": flagged,
                "errors": errors,
                "flagged_parties": flagged_parties,
            }

        except Exception as e:
            logger.exception("konkurs_monitor: fatal error: %s", e)
            return {"status": "error", "message": str(e)}


async def get_flagged_parties(db: AsyncSession) -> list[dict]:
    """
    Return all parties that have risk flags (CRITICAL or WARNING), sorted by severity.
    """
    from sqlalchemy import text

    sql = text("""
        SELECT
            p.party_id,
            p.name,
            p.orgnr,
            p.external_data -> 'konkurs_status' AS ks_data,
            COUNT(c.contract_id) FILTER (WHERE c.status = 'active') AS active_contracts
        FROM parties p
        LEFT JOIN contracts c ON c.party_id = p.party_id
        WHERE p.external_data IS NOT NULL
          AND (p.external_data -> 'konkurs_status') ->> 'risk_level' IN ('CRITICAL', 'WARNING')
        GROUP BY p.party_id, p.name, p.orgnr
        ORDER BY
            CASE (p.external_data -> 'konkurs_status') ->> 'risk_level'
                WHEN 'CRITICAL' THEN 0
                WHEN 'WARNING' THEN 1
                ELSE 2
            END,
            p.name
    """)
    rows = (await db.execute(sql)).fetchall()

    import json as _json
    results = []
    for row in rows:
        raw = row.ks_data
        if isinstance(raw, str):
            try:
                raw = _json.loads(raw)
            except Exception:
                raw = {}
        s = raw or {}
        results.append({
            "party_id": str(row.party_id),
            "name": row.name,
            "orgnr": row.orgnr,
            "active_contracts": row.active_contracts or 0,
            "risk_level": s.get("risk_level", "OK"),
            "risk_flags": s.get("risk_flags", []),
            "konkurs": s.get("konkurs", False),
            "under_avvikling": s.get("under_avvikling", False),
            "under_tvangsavvikling": s.get("under_tvangsavvikling", False),
            "slettet": s.get("slettet", False),
            "mangler_regnskap": s.get("mangler_regnskap", False),
            "siste_regnskap_aar": s.get("siste_regnskap_aar"),
            "checked_at": s.get("checked_at"),
        })
    return results
