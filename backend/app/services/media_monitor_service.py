"""
Media Monitor Service – nightly sentiment analysis for all active tenants.

For each party with orgnr + active contracts:
  1. DuckDuckGo search: company name + "nyheter" + negative/positive terms
  2. GPT-4o sentiment analysis → score 1–10, red_flags, positive_news, summary
  3. Store in party.external_data.media_monitoring

Run nightly via APScheduler (see main.py) or manually via:
  POST /api/v1/media-monitor/run-all
"""
import logging
import asyncio
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

logger = logging.getLogger(__name__)

# ── Sentinel so we can run at most one job at a time ────────────────────────
_job_running = False


async def _search_news(company_name: str, orgnr: str, *, is_barnevern_tenant: bool = False) -> list[dict]:
    """Run DuckDuckGo queries and return merged results (max 10 snippets).
    For barnevern-tenants: adds extra queries (tilsyn, avvik, Bufdir) for leietakere av barnevernsinstitusjoner.
    """
    from app.services.mcp.handler import search_web_tool  # lazy import

    queries = [
        f'"{company_name}" nyheter',
        f'"{company_name}" {orgnr} negativ OR positiv OR tilbakemelding',
    ]
    if is_barnevern_tenant:
        queries.extend([
            f'"{company_name}" barnevern tilsyn OR avvik',
            f'"{company_name}" Bufdir Bufetat tilbakemelding',
        ])
    results: list[dict] = []
    for q in queries:
        try:
            hits = await search_web_tool(query=q, max_results=5)
            if isinstance(hits, list):
                results.extend(hits)
        except Exception as e:
            logger.debug("media_monitor: search failed for %r: %s", q, e)
    # Deduplicate by href
    seen: set[str] = set()
    unique: list[dict] = []
    for r in results:
        href = r.get("href", "")
        if href and href not in seen:
            seen.add(href)
            unique.append(r)
    return unique[:10]


async def _analyze_sentiment(company_name: str, orgnr: str, snippets: list[dict]) -> dict:
    """Use GPT-4o to analyse sentiment of search results for a company."""
    if not snippets:
        return {
            "sentiment_score": 5,
            "sentiment_label": "Nøytralt",
            "summary": "Ingen nyhetstreff funnet.",
            "red_flags": [],
            "positive_news": [],
            "sources_checked": 0,
        }

    from openai import AsyncOpenAI
    from app.core.config import settings

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    snippets_text = "\n\n".join(
        f"[{i+1}] {r.get('title','')}\n{r.get('href','')}\n{r.get('body','')[:400]}"
        for i, r in enumerate(snippets)
    )

    prompt = f"""Du er en norsk kreditt- og omdømmeanalytiker.

Analyser følgende nyhetsresultater om selskapet "{company_name}" (org.nr {orgnr}).

SØKERESULTATER:
{snippets_text}

Returner KUN gyldig JSON med følgende felter (ingen forklaring rundt):
{{
  "sentiment_score": <tall 1–10, der 1=veldig negativt, 5=nøytralt, 10=veldig positivt>,
  "sentiment_label": <"Negativt"|"Nøytralt"|"Positivt">,
  "summary": <1–2 setninger norsk oppsummering>,
  "red_flags": [<maks 5 korte norske strenger om negative funn>],
  "positive_news": [<maks 3 korte norske strenger om positive funn>]
}}"""

    try:
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=500,
            ),
            timeout=30.0,
        )
        import json
        result = json.loads(resp.choices[0].message.content or "{}")
        result["sources_checked"] = len(snippets)
        return result
    except Exception as e:
        logger.warning("media_monitor: GPT analysis failed for %s: %s", company_name, e)
        return {
            "sentiment_score": 5,
            "sentiment_label": "Nøytralt",
            "summary": "Analyse feilet.",
            "red_flags": [],
            "positive_news": [],
            "sources_checked": len(snippets),
        }


async def _is_barnevern_tenant(db: AsyncSession, party_id: str) -> bool:
    """Check if party has active contracts with barnevern properties."""
    sql = text("""
        SELECT 1 FROM contracts c
        JOIN units u ON c.unit_id = u.unit_id
        JOIN properties pr ON u.property_id = pr.property_id
        WHERE c.party_id = :pid AND c.status = 'active'
        AND (
          pr.usage ILIKE '%barnevern%'
          OR pr.unit_type_derived ILIKE '%barnevern%'
          OR pr.unit_short_type ILIKE '%barnevern%'
        )
        LIMIT 1
    """)
    row = (await db.execute(sql, {"pid": party_id})).fetchone()
    return row is not None


async def monitor_single_party(db: AsyncSession, party_id: str) -> Optional[dict]:
    """Run media monitoring for one party. Returns the result dict or None."""
    from app.domains.core.models.party import Party

    result_q = await db.execute(select(Party).where(Party.party_id == party_id))
    party = result_q.scalar_one_or_none()
    if not party or not party.orgnr:
        return None

    is_bv = await _is_barnevern_tenant(db, party_id)
    snippets = await _search_news(party.name, party.orgnr, is_barnevern_tenant=is_bv)
    analysis = await _analyze_sentiment(party.name, party.orgnr, snippets)
    analysis["last_updated"] = datetime.now(timezone.utc).isoformat()

    ext = dict(party.external_data or {})
    ext["media_monitoring"] = analysis
    party.external_data = ext
    await db.commit()
    return analysis


async def run_all_active_tenants(db: AsyncSession, limit: int = 200) -> dict:
    """
    Run media monitoring for all parties with:
      - orgnr set
      - at least one active contract
    Processes in batches of 5 with 2s delay between batches.
    Returns summary stats.
    """
    global _job_running
    if _job_running:
        logger.info("media_monitor: job already running, skipping")
        return {"status": "already_running"}

    _job_running = True
    logger.info("media_monitor: starting nightly run")

    try:
        # Fetch party IDs with active contracts + barnevern-flag for leietakere av barnevernsinstitusjoner
        sql = text("""
            SELECT DISTINCT p.party_id, p.name, p.orgnr,
              EXISTS (
                SELECT 1 FROM contracts c2
                JOIN units u ON c2.unit_id = u.unit_id
                JOIN properties pr ON u.property_id = pr.property_id
                WHERE c2.party_id = p.party_id AND c2.status = 'active'
                AND (
                  pr.usage ILIKE '%barnevern%'
                  OR pr.unit_type_derived ILIKE '%barnevern%'
                  OR pr.unit_short_type ILIKE '%barnevern%'
                )
              ) AS is_barnevern_tenant
            FROM parties p
            JOIN contracts c ON c.party_id = p.party_id
            WHERE p.orgnr IS NOT NULL
              AND c.status = 'active'
            LIMIT :limit
        """)
        rows = (await db.execute(sql, {"limit": limit})).fetchall()

        total = len(rows)
        done = updated = errors = 0

        for i, row in enumerate(rows):
            try:
                is_bv = bool(getattr(row, "is_barnevern_tenant", False))
                snippets = await _search_news(row.name, row.orgnr, is_barnevern_tenant=is_bv)
                analysis = await _analyze_sentiment(row.name, row.orgnr, snippets)
                analysis["last_updated"] = datetime.now(timezone.utc).isoformat()

                await db.execute(
                    text("""
                        UPDATE parties
                        SET external_data = jsonb_set(
                            COALESCE(external_data, '{}'::jsonb),
                            '{media_monitoring}',
                            :payload::jsonb
                        )
                        WHERE party_id = :party_id
                    """),
                    {
                        "party_id": str(row.party_id),
                        "payload": __import__("json").dumps(analysis),
                    },
                )
                updated += 1
            except Exception as e:
                logger.warning("media_monitor: failed for %s (%s): %s", row.name, row.orgnr, e)
                errors += 1
            done += 1

            # Commit every 10 + throttle 5 per batch
            if done % 10 == 0:
                await db.commit()
                logger.info("media_monitor: %d/%d done", done, total)
            if done % 5 == 0:
                await asyncio.sleep(2)

        await db.commit()
        logger.info("media_monitor: finished – %d updated, %d errors", updated, errors)
        return {"status": "ok", "total": total, "updated": updated, "errors": errors}

    except Exception as e:
        logger.exception("media_monitor: fatal error: %s", e)
        return {"status": "error", "message": str(e)}
    finally:
        _job_running = False


async def get_tenant_sentiment_ranking(db: AsyncSession) -> list[dict]:
    """
    Return all parties with media_monitoring data, sorted by sentiment_score ASC
    (most negative first).
    """
    sql = text("""
        SELECT
            p.party_id,
            p.name,
            p.orgnr,
            p.external_data -> 'media_monitoring' AS media,
            COUNT(c.contract_id) FILTER (WHERE c.status = 'active') AS active_contracts
        FROM parties p
        LEFT JOIN contracts c ON c.party_id = p.party_id
        WHERE p.external_data ? 'media_monitoring'
          AND (p.external_data -> 'media_monitoring') ->> 'last_updated' IS NOT NULL
        GROUP BY p.party_id, p.name, p.orgnr
        ORDER BY (p.external_data -> 'media_monitoring' ->> 'sentiment_score')::float ASC NULLS LAST
    """)
    rows = (await db.execute(sql)).fetchall()

    results = []
    for row in rows:
        media = row.media or {}
        results.append({
            "party_id": str(row.party_id),
            "name": row.name,
            "orgnr": row.orgnr,
            "active_contracts": row.active_contracts or 0,
            "sentiment_score": media.get("sentiment_score", 5),
            "sentiment_label": media.get("sentiment_label", "Nøytralt"),
            "summary": media.get("summary", ""),
            "red_flags": media.get("red_flags", []),
            "positive_news": media.get("positive_news", []),
            "sources_checked": media.get("sources_checked", 0),
            "last_updated": media.get("last_updated"),
        })
    return results
