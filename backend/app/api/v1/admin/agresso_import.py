"""
Agresso import og budsjett-vs-regnskap-analyse.

Endepunkter:
  POST /admin/agresso/import-budsjett   – importer Budsjett 2025_2026-arket
  POST /admin/agresso/import-kontant    – importer Kontant 2025 (ny format, m/dedup)
  GET  /admin/agresso/budget-vs-actual  – 3-veis sammenligning
  GET  /admin/agresso/lokaler-avstemming – GL Lokaler vs kontraktsfestet husleie
  GET  /admin/agresso/import-status     – vis importede batch-er

KRITISKE REGLER (CLAUDE.md §7-12):
- GROUP BY ... HAVING SUM(belop) != 0, aldri WHERE belop > 0
- Ekskluder 'Statlig'-eiendommer fra regional analyse
- belop/ar (ikke amount/year)
"""

import io
import logging
import uuid
from datetime import datetime
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.domains.core.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agresso", tags=["agresso"])

# Bufdir 2027-inndeling – identiske med economic_import.py
LOKALER_KONTOER = {"6300", "6310", "6390", "6391", "6395", "6396", "6398"}
VEDLIKEHOLD_KONTOER = {"1268", "4960", "6630", "6632", "6662"}
GJENNOMSTROMNING_BILAGSARTER = {"H1", "H2", "HB", "RE"}


def _srs_kategori(konto: str, ba_kode: str = "") -> str:
    if ba_kode.upper() in GJENNOMSTROMNING_BILAGSARTER:
        return "Gjennomstrømning"
    if konto in LOKALER_KONTOER:
        return "Lokaler"
    if konto in VEDLIKEHOLD_KONTOER:
        return "Vedlikehold"
    return "Drift"


def _safe_str(v) -> Optional[str]:
    if pd.isna(v):
        return None
    return str(int(float(v))) if isinstance(v, (int, float)) else str(v).strip() or None


def _safe_num(v) -> Optional[float]:
    try:
        return float(v) if pd.notna(v) else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# IMPORT: Budsjett 2025_2026
# ---------------------------------------------------------------------------

@router.post("/import-budsjett")
async def import_agresso_budsjett(
    file: UploadFile = File(...),
    sheet_name: str = Query(default="Budsjett 2025_2026"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Importer Agresso-budsjett fra Excel (Budsjett 2025_2026-arket).
    Kolonner: Konto, Konto(T), Koststed, Koststed(T), Prosjekt, Prosjekt(T),
              Finansiering, Finansiering(T), Periode, Beløp DA, Kontantbeløp
    """
    if current_user.role not in ("ADMIN",):
        raise HTTPException(status_code=403, detail="Kun ADMIN kan importere budsjettdata")

    contents = await file.read()
    try:
        df = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Kunne ikke lese Excel: {e}")

    df = df.dropna(subset=["Konto", "Periode"])
    batch_id = f"budsjett_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename or 'upload'}"

    # Slett evt. eksisterende batch for samme år/fil (idempotent)
    await db.execute(
        text("DELETE FROM agresso_budgets WHERE batch_id = :bid"),
        {"bid": batch_id},
    )

    # Bygg property_id-oppslag: koststed_kode (dim1_kode) → property_id
    prop_map = await _build_property_map(db)

    rows_inserted = 0
    errors = 0
    for _, row in df.iterrows():
        try:
            konto = _safe_str(row["Konto"])
            if not konto:
                continue
            periode_raw = _safe_str(row["Periode"])
            if not periode_raw or len(periode_raw) < 6:
                continue
            ar = int(periode_raw[:4])
            maaned = int(periode_raw[4:6])
            koststed = _safe_str(row.get("Koststed"))
            property_id = prop_map.get(koststed)

            await db.execute(text("""
                INSERT INTO agresso_budgets
                  (id, konto, konto_navn, koststed_kode, koststed_navn,
                   prosjekt_kode, prosjekt_navn, finansiering_kode, finansiering_navn,
                   periode, ar, maaned, belop_da, kontantbelop, srs_kategori,
                   property_id, batch_id, imported_by, source_file_ref, created_at)
                VALUES
                  (:id, :konto, :konto_navn, :koststed_kode, :koststed_navn,
                   :prosjekt_kode, :prosjekt_navn, :finansiering_kode, :finansiering_navn,
                   :periode, :ar, :maaned, :belop_da, :kontantbelop, :srs_kategori,
                   :property_id, :batch_id, :imported_by, :source_file_ref, NOW())
            """), {
                "id": str(uuid.uuid4()),
                "konto": konto,
                "konto_navn": _safe_str(row.get("Konto(T)")),
                "koststed_kode": koststed,
                "koststed_navn": _safe_str(row.get("Koststed(T)")),
                "prosjekt_kode": _safe_str(row.get("Prosjekt")),
                "prosjekt_navn": _safe_str(row.get("Prosjekt(T)")),
                "finansiering_kode": _safe_str(row.get("Finansiering")),
                "finansiering_navn": _safe_str(row.get("Finansiering(T)")),
                "periode": periode_raw[:6],
                "ar": ar,
                "maaned": maaned,
                "belop_da": _safe_num(row.get("Beløp DA")),
                "kontantbelop": _safe_num(row.get("Kontantbeløp")),
                "srs_kategori": _srs_kategori(konto),
                "property_id": property_id,
                "batch_id": batch_id,
                "imported_by": current_user.email,
                "source_file_ref": file.filename,
            })
            rows_inserted += 1
        except Exception as e:
            logger.warning(f"Budsjett-import feil rad {_}: {e}")
            errors += 1

    await db.commit()
    logger.info(f"Agresso budsjett importert: {rows_inserted} rader, {errors} feil. Batch: {batch_id}")
    return {
        "status": "ok",
        "batch_id": batch_id,
        "rows_inserted": rows_inserted,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# IMPORT: Kontant 2025 (ny format, med deduplication mot gl_transactions)
# ---------------------------------------------------------------------------

@router.post("/import-kontant")
async def import_agresso_kontant(
    file: UploadFile = File(...),
    sheet_name: str = Query(default="Kontant 2025"),
    dry_run: bool = Query(default=True, description="True = kun teller, False = importerer"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Importer Agresso kontantregnskap (Kontant 2025-arket) til gl_transactions.
    Utfører deduplisering: hopper over rader der bilagsnr+periode+konto+dim1_kode allerede finnes.
    Kolonner: Konto, Konto(T), Avdeling (=Dim1), Avdeling(T), Statskonto, Dim 2, Dim 2(T),
              Målgruppe, BA, Bilagsnr, Resk.nr, Resk.nr(T), Tekst, Formål (=Dim3),
              Kontantbeløp, Kont.periode
    """
    if current_user.role not in ("ADMIN",):
        raise HTTPException(status_code=403, detail="Kun ADMIN kan importere GL-data")

    contents = await file.read()
    try:
        df = pd.read_excel(io.BytesIO(contents), sheet_name=sheet_name, dtype=str)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Kunne ikke lese Excel: {e}")

    # Filtrer ut ugyldige rader (Konto må være 4-sifret tall)
    df = df[df["Konto"].str.match(r"^\d{4}$", na=False)]
    df = df.dropna(subset=["Kontantbeløp", "Kont.periode"])

    batch_id = f"kontant_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename or 'upload'}"
    prop_map = await _build_property_map(db)

    skipped = 0
    inserted = 0
    errors = 0

    for _, row in df.iterrows():
        try:
            konto = row["Konto"].strip()
            periode_raw = str(row["Kont.periode"]).strip().replace(".0", "")[:6]
            if len(periode_raw) < 6:
                continue
            ar = int(periode_raw[:4])
            dim1_kode = str(row.get("Avdeling", "") or "").strip().replace(".0", "") or None
            bilagsnr = str(row.get("Bilagsnr", "") or "").strip() or None
            belop_raw = row.get("Kontantbeløp", "0").replace(",", ".").strip()
            belop = float(belop_raw) if belop_raw else 0.0
            ba_kode = str(row.get("BA", "") or "").strip() or None

            # Deduplisering mot gl_transactions
            if bilagsnr and dim1_kode:
                dup = await db.execute(text("""
                    SELECT 1 FROM gl_transactions
                    WHERE bilagsnr = :bnr AND periode = :per AND konto = :knt AND dim1_kode = :d1
                    LIMIT 1
                """), {"bnr": bilagsnr, "per": periode_raw, "knt": konto, "d1": dim1_kode})
                if dup.fetchone():
                    skipped += 1
                    continue

            if dry_run:
                inserted += 1
                continue

            dim3_kode = str(row.get("Formål", "") or "").strip().replace(".0", "") or None
            property_id = prop_map.get(dim1_kode)

            await db.execute(text("""
                INSERT INTO gl_transactions
                  (transaction_id, konto, konto_navn, dim1_kode, dim1_navn,
                   av_konto, dim2_kode, dim2_navn, dim3_kode, ba_kode,
                   bilagsnr, leverandor_id, leverandor_navn, tekst,
                   belop, periode, ar, maaned, srs_kategori, property_id,
                   batch_id, imported_by, source_file_ref)
                VALUES
                  (:tid, :konto, :konto_navn, :dim1_kode, :dim1_navn,
                   :av_konto, :dim2_kode, :dim2_navn, :dim3_kode, :ba_kode,
                   :bilagsnr, :leverandor_id, :leverandor_navn, :tekst,
                   :belop, :periode, :ar, :maaned, :srs_kategori, :property_id,
                   :batch_id, :imported_by, :source_file_ref)
                ON CONFLICT DO NOTHING
            """), {
                "tid": str(uuid.uuid4()),
                "konto": konto,
                "konto_navn": str(row.get("Konto(T)", "") or "").strip() or None,
                "dim1_kode": dim1_kode,
                "dim1_navn": str(row.get("Avdeling(T)", "") or "").strip() or None,
                "av_konto": str(row.get("Statskonto", "") or "").strip() or None,
                "dim2_kode": str(row.get("Dim 2", "") or "").strip().replace(".0", "") or None,
                "dim2_navn": str(row.get("Dim 2(T)", "") or "").strip() or None,
                "dim3_kode": dim3_kode,
                "ba_kode": ba_kode,
                "bilagsnr": bilagsnr,
                "leverandor_id": str(row.get("Resk.nr", "") or "").strip() or None,
                "leverandor_navn": str(row.get("Resk.nr(T)", "") or "").strip() or None,
                "tekst": str(row.get("Tekst", "") or "").strip()[:500] or None,
                "belop": belop,
                "periode": periode_raw,
                "ar": ar,
                "maaned": int(periode_raw[4:6]),
                "srs_kategori": _srs_kategori(konto, ba_kode or ""),
                "property_id": property_id,
                "batch_id": batch_id,
                "imported_by": current_user.email,
                "source_file_ref": file.filename,
            })
            inserted += 1
        except Exception as e:
            logger.warning(f"Kontant-import feil rad {_}: {e}")
            errors += 1

    if not dry_run:
        await db.commit()

    return {
        "status": "dry_run" if dry_run else "ok",
        "batch_id": batch_id if not dry_run else None,
        "rows_would_insert": inserted if dry_run else None,
        "rows_inserted": inserted if not dry_run else None,
        "rows_skipped_duplicate": skipped,
        "errors": errors,
        "message": "Kjør med dry_run=false for å importere" if dry_run else f"Importert {inserted} rader",
    }


# ---------------------------------------------------------------------------
# ANALYSE: Budget vs Actual (3-veis)
# ---------------------------------------------------------------------------

@router.get("/budget-vs-actual")
async def budget_vs_actual(
    ar: int = Query(default=2025, description="År (2025 eller 2026)"),
    srs_kategori: Optional[str] = Query(default=None, description="Lokaler|Drift|Vedlikehold"),
    region: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    3-veis sammenligning per srs_kategori og region:
      (A) Agresso offisielt budsjett (agresso_budgets)
      (B) Faktisk regnskap GL (gl_transactions) — netto, ekskl Gjennomstrømning
      (C) Våre estimater (property_annual_costs) — kpi_adjusted_rent + vedlikehold osv.

    Differanser:
      Avvik B-A = Regnskap vs Agresso-budsjett
      Avvik C-A = Våre estimater vs Agresso-budsjett
    """
    srs_filter = "AND g.srs_kategori = :srs" if srs_kategori else ""
    region_filter = "AND p.region ILIKE :region" if region else ""
    params = {"ar": ar}
    if srs_kategori:
        params["srs"] = srs_kategori
    if region:
        params["region"] = f"%{region}%"

    # (A) Agresso-budsjett per srs_kategori
    budsjett_q = await db.execute(text(f"""
        SELECT b.srs_kategori,
               COALESCE(p.region, 'Ukjent') AS region,
               SUM(b.kontantbelop) AS budsjett_agresso
        FROM agresso_budgets b
        LEFT JOIN properties p ON p.property_id = b.property_id
        WHERE b.ar = :ar AND b.srs_kategori != 'Gjennomstrømning'
        {'AND b.srs_kategori = :srs' if srs_kategori else ''}
        {'AND p.region ILIKE :region' if region else ''}
        GROUP BY b.srs_kategori, p.region
        HAVING SUM(b.kontantbelop) != 0
        ORDER BY b.srs_kategori, p.region
    """), params)
    budsjett_rows = budsjett_q.fetchall()

    # (B) GL Faktisk per srs_kategori — netto, ekskl Gjennomstrømning, ekskl Statlig
    gl_q = await db.execute(text(f"""
        SELECT g.srs_kategori,
               COALESCE(p.region, g.region, 'Ukjent') AS region,
               SUM(g.belop) AS regnskap_gl
        FROM gl_transactions g
        LEFT JOIN properties p ON p.property_id = g.property_id
        WHERE g.ar = :ar
          AND g.srs_kategori != 'Gjennomstrømning'
          AND (p.name IS NULL OR p.name != 'Statlig')
          {srs_filter}
          {region_filter}
        GROUP BY g.srs_kategori, p.region, g.region
        HAVING SUM(g.belop) != 0
        ORDER BY g.srs_kategori
    """), params)
    gl_rows = gl_q.fetchall()

    # (C) Egne estimater (property_annual_costs) — totalt per år
    pac_q = await db.execute(text(f"""
        SELECT
          COALESCE(p.region, 'Ukjent') AS region,
          SUM(pac.kpi_adjusted_rent) AS estimat_husleie,
          SUM(COALESCE(pac.internal_maintenance,0) + COALESCE(pac.common_costs,0) +
              COALESCE(pac.energy_costs,0) + COALESCE(pac.heating_costs,0) +
              COALESCE(pac.cleaning_costs,0) + COALESCE(pac.parking_rent,0) +
              COALESCE(pac.caretaker_cost,0)) AS estimat_drift_vedlikehold
        FROM property_annual_costs pac
        JOIN properties p ON p.property_id = pac.property_id
        WHERE pac.year = :ar AND p.name != 'Statlig'
        {region_filter}
        GROUP BY p.region
        ORDER BY p.region
    """), params)
    pac_rows = pac_q.fetchall()

    # Bygg svar
    budsjett_map = {(r.srs_kategori, r.region): float(r.budsjett_agresso or 0) for r in budsjett_rows}
    gl_map = {}
    for r in gl_rows:
        key = (r.srs_kategori, r.region)
        gl_map[key] = gl_map.get(key, 0) + float(r.regnskap_gl or 0)

    # Aggregat per srs_kategori (alle regioner)
    srs_summary = {}
    for (srs, reg), b_val in budsjett_map.items():
        if srs not in srs_summary:
            srs_summary[srs] = {"budsjett_agresso": 0, "regnskap_gl": 0}
        srs_summary[srs]["budsjett_agresso"] += b_val
    for (srs, reg), g_val in gl_map.items():
        if srs not in srs_summary:
            srs_summary[srs] = {"budsjett_agresso": 0, "regnskap_gl": 0}
        srs_summary[srs]["regnskap_gl"] += g_val

    # Egne estimater totalt
    estimat_husleie = sum(float(r.estimat_husleie or 0) for r in pac_rows)
    estimat_drift = sum(float(r.estimat_drift_vedlikehold or 0) for r in pac_rows)

    result_summary = []
    for srs, vals in sorted(srs_summary.items()):
        a = vals["budsjett_agresso"]
        b = vals["regnskap_gl"]
        result_summary.append({
            "srs_kategori": srs,
            "budsjett_agresso_kr": round(a),
            "regnskap_gl_kr": round(b),
            "avvik_regnskap_vs_budsjett_kr": round(b - a),
            "avvik_pct": round((b - a) / a * 100, 1) if a else None,
        })

    return {
        "ar": ar,
        "sammendrag": result_summary,
        "egne_estimater": {
            "estimat_husleie_kr": round(estimat_husleie),
            "estimat_drift_vedlikehold_kr": round(estimat_drift),
            "kommentar": "Fra property_annual_costs (BEFS egne estimater, ikke GL-basert)",
        },
        "sammenligning_estimater_vs_agresso": {
            "lokaler": {
                "agresso_budsjett_kr": round(srs_summary.get("Lokaler", {}).get("budsjett_agresso", 0)),
                "vare_estimater_kr": round(estimat_husleie),
                "avvik_kr": round(estimat_husleie - srs_summary.get("Lokaler", {}).get("budsjett_agresso", 0)),
            }
        },
        "note": "Agresso-budsjett: offisiell, GL-regnskap: netto ekskl Gjennomstrømning og Statlig",
    }


# ---------------------------------------------------------------------------
# ANALYSE: Lokaler-avstemming GL vs Kontrakter
# ---------------------------------------------------------------------------

@router.get("/lokaler-avstemming")
async def lokaler_avstemming(
    ar: int = Query(default=2025),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Tiltak 4 (fra plan): Sammenlign GL Lokaler-kostnader mot kontraktsfestet husleie.
    Kontrakter er fasit (per Frank/Eivind avtale).

    Per eiendom:
      GL Lokaler netto (srs_kategori='Lokaler', ekskl Gjennomstrømning)
      Kontraktsfestet (kpi_adjusted_rent fra property_annual_costs)
      Avvik = GL - Kontrakt
      Agresso-budsjett Lokaler (agresso_budgets)
    """
    q = await db.execute(text("""
        WITH gl_lokaler AS (
            SELECT g.property_id,
                   SUM(g.belop) AS gl_lokaler
            FROM gl_transactions g
            WHERE g.ar = :ar
              AND g.srs_kategori = 'Lokaler'
              AND g.ba_kode NOT IN ('H1','H2','HB','RE')
            GROUP BY g.property_id
            HAVING SUM(g.belop) != 0
        ),
        kontraktsleie AS (
            SELECT pac.property_id,
                   SUM(pac.kpi_adjusted_rent) AS kontraktsleie
            FROM property_annual_costs pac
            WHERE pac.year = :ar
            GROUP BY pac.property_id
        ),
        agresso_bud AS (
            SELECT b.property_id,
                   SUM(b.kontantbelop) AS budsjett_agresso
            FROM agresso_budgets b
            WHERE b.ar = :ar AND b.srs_kategori = 'Lokaler'
            GROUP BY b.property_id
            HAVING SUM(b.kontantbelop) != 0
        )
        SELECT
            p.property_id::text,
            p.name,
            p.region,
            COALESCE(gl.gl_lokaler, 0) AS gl_lokaler,
            COALESCE(kl.kontraktsleie, 0) AS kontraktsleie,
            COALESCE(ab.budsjett_agresso, 0) AS budsjett_agresso,
            COALESCE(gl.gl_lokaler, 0) - COALESCE(kl.kontraktsleie, 0) AS avvik_gl_vs_kontrakt,
            COALESCE(gl.gl_lokaler, 0) - COALESCE(ab.budsjett_agresso, 0) AS avvik_gl_vs_budsjett
        FROM properties p
        LEFT JOIN gl_lokaler gl ON gl.property_id = p.property_id
        LEFT JOIN kontraktsleie kl ON kl.property_id = p.property_id
        LEFT JOIN agresso_bud ab ON ab.property_id = p.property_id
        WHERE (gl.gl_lokaler IS NOT NULL OR kl.kontraktsleie IS NOT NULL)
          AND p.name != 'Statlig'
        ORDER BY ABS(COALESCE(gl.gl_lokaler,0) - COALESCE(kl.kontraktsleie,0)) DESC
        LIMIT 50
    """), {"ar": ar})
    rows = q.fetchall()

    items = []
    for r in rows:
        gl = float(r.gl_lokaler)
        kl = float(r.kontraktsleie)
        bud = float(r.budsjett_agresso)
        avvik_pct = round((float(r.avvik_gl_vs_kontrakt) / kl * 100), 1) if kl else None
        items.append({
            "property_id": r.property_id,
            "name": r.name,
            "region": r.region,
            "gl_lokaler_kr": round(gl),
            "kontraktsleie_kr": round(kl),
            "budsjett_agresso_kr": round(bud),
            "avvik_gl_vs_kontrakt_kr": round(float(r.avvik_gl_vs_kontrakt)),
            "avvik_gl_vs_kontrakt_pct": avvik_pct,
            "avvik_gl_vs_budsjett_kr": round(float(r.avvik_gl_vs_budsjett)),
            "flagg": "⚠️ Stort avvik" if abs(float(r.avvik_gl_vs_kontrakt)) > 100_000 else "✅ OK",
        })

    total_gl = sum(i["gl_lokaler_kr"] for i in items)
    total_kl = sum(i["kontraktsleie_kr"] for i in items)
    total_bud = sum(i["budsjett_agresso_kr"] for i in items)

    return {
        "ar": ar,
        "totalt": {
            "gl_lokaler_kr": total_gl,
            "kontraktsleie_kr": total_kl,
            "budsjett_agresso_kr": total_bud,
            "avvik_gl_vs_kontrakt_kr": total_gl - total_kl,
            "avvik_gl_vs_budsjett_kr": total_gl - total_bud,
            "note": "Kontrakter er fasit (per Frank/Eivind avtale). Avvik > 0 betyr GL er høyere enn kontraktsleie.",
        },
        "per_eiendom": items,
    }


# ---------------------------------------------------------------------------
# IMPORT: Kontant 2026 → finance_budget (data_source='kontant_2026')
# ---------------------------------------------------------------------------

@router.post("/import-kontant-2026")
async def import_kontant_2026(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Importer økonomi sitt kontantregnskap for 2026 (jan-apr) til finance_budget-tabellen
    som data_source='kontant_2026'. Idempotent: sletter og re-inserter.
    Excel-fanen skal hete 'Kontant 2026' eller 'Kontant'.
    """
    if current_user.role not in ("ADMIN",):
        raise HTTPException(status_code=403, detail="Kun ADMIN kan importere kontantdata")

    from app.services.finance_budget_import_service import import_kontant_actuals
    contents = await file.read()
    try:
        report = await import_kontant_actuals(
            db=db,
            file_content=contents,
            filename=file.filename or "kontant_2026.xlsx",
            imported_by=current_user.email or "admin",
            year=2026,
        )
    except Exception as e:
        logger.exception("import-kontant-2026 feilet: %s", e)
        raise HTTPException(status_code=500, detail=f"Import feilet: {e}")

    return {
        "status": "ok",
        "inserted": report.inserted,
        "skipped_zero_amount": report.skipped_zero_amount,
        "unmatched_koststeder": len(report.unmatched_koststeder),
        "total_2026_nok": report.total_2025_nok,  # field name is 2025 in service but holds current year sum
    }


# ---------------------------------------------------------------------------
# STATUS: vis importede batch-er
# ---------------------------------------------------------------------------

@router.get("/import-status")
async def import_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = await db.execute(text("""
        SELECT batch_id, ar, srs_kategori,
               COUNT(*) AS rader,
               SUM(kontantbelop) AS total_belop,
               MAX(created_at) AS importert
        FROM agresso_budgets
        GROUP BY batch_id, ar, srs_kategori
        ORDER BY MAX(created_at) DESC
        LIMIT 30
    """))
    rows = q.fetchall()
    return {
        "agresso_budgets": [
            {
                "batch_id": r.batch_id,
                "ar": r.ar,
                "srs_kategori": r.srs_kategori,
                "rader": r.rader,
                "total_belop_kr": round(float(r.total_belop or 0)),
                "importert": str(r.importert),
            }
            for r in rows
        ]
    }


# ---------------------------------------------------------------------------
# Hjelpefunksjon: bygg dim1_kode → property_id-kart
# ---------------------------------------------------------------------------

async def _build_property_map(db: AsyncSession) -> dict:
    """
    Matcher Agresso koststed/avdeling (dim1_kode) mot property via unit_id_erp.
    Returnerer {dim1_kode_str: property_id_str}.
    """
    try:
        r = await db.execute(text("""
            SELECT DISTINCT ON (p.unit_id_erp) p.unit_id_erp, p.property_id::text
            FROM properties p
            WHERE p.unit_id_erp IS NOT NULL
        """))
        return {str(row.unit_id_erp): row.property_id for row in r.fetchall()}
    except Exception as e:
        logger.warning(f"Kunne ikke bygge property-map: {e}")
        return {}
