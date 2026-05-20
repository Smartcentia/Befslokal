"""
Admin endpoints for importing and managing economic/financial data.
"""
import csv
import io
import os
import uuid
import asyncio
import datetime
import logging
import pandas as pd
from decimal import Decimal, InvalidOperation
from typing import Any
from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.api.deps import get_db, get_current_active_superuser
from app.services.data_management import DataManagementService
from app.domains.core.models.property import Property

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/economic-import",
    dependencies=[Depends(get_current_active_superuser)],
)

# ---------------------------------------------------------------------------
# In-memory job status (single-process; fine for one-time imports)
# ---------------------------------------------------------------------------
_gl_import_status: dict[str, Any] = {"state": "idle", "message": "Ingen import kjører"}


# ---------------------------------------------------------------------------
# Agresso SRS-helpers (mirrors backend/scripts/import_gl_agresso.py)
# ---------------------------------------------------------------------------
GJENNOMSTRØMNING_BILAGSARTER = {"H1", "H2", "HB", "RE"}
ANLEGG_KONTOER = {
    "1268", "4960",
    "1040", "1049", "1050", "1059", "1060", "1069", "1070", "1079",
    "1080", "1089", "1090", "1099", "1200", "1209", "1210", "1219",
    "1220", "1229", "1230", "1239", "1240", "1249", "1250", "1259",
    "1260", "1269", "1270", "1279", "1280", "1289", "1290", "1298",
    "3800", "3801", "3810",
    "4930", "4960", "4990", "4999",
    "6000", "6010", "6020", "6030", "6040", "6050", "6060", "6071",
    "6551", "7800",
}


def _bestem_srs_kategori(konto: str, ba_kode: str) -> str:
    """SRS-kategorisering per SRS 17:
    - Gjennomstrømning: bilagsarter H1/H2/HB/RE (omposteringer/reverseringer)
    - Investering: konto 1268 (kjøp fast eiendom) + hele 4930–4999-serien (anleggsinvesteringer)
    - Drift: alt annet (6xxx lokalkostnader etc.)
    """
    if ba_kode.upper() in GJENNOMSTRØMNING_BILAGSARTER:
        return "Gjennomstrømning"
    try:
        konto_int = int(konto)
        if konto_int == 1268 or (4930 <= konto_int <= 4999):
            return "Investering"
    except (ValueError, TypeError):
        pass
    return "Drift"


def _rens_belop(raw: str) -> Decimal | None:
    if not raw or not raw.strip():
        return None
    s = raw.strip()
    negative = s.startswith("(") and s.endswith(")")
    if negative:
        s = s[1:-1]
    s = s.replace(",", "").replace(" ", "")
    try:
        val = Decimal(s)
        return -val if negative else val
    except InvalidOperation:
        return None


def _parse_dato(raw: str) -> datetime.date | None:
    if not raw or not raw.strip():
        return None
    for fmt in ("%m/%d/%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    return None


@router.post("/preview")
async def preview_financial_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Dry-run: parse a Xledger/Visma CSV and show property-matching stats
    without writing anything to the database.
    """
    content = await file.read()

    try:
        for encoding in ("utf-8-sig", "windows-1252", "latin-1", "utf-8"):
            try:
                sample = content[:1000].decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            sample = content[:1000].decode("utf-8", errors="replace")
        delimiter = ";" if ";" in sample else ","
        df = pd.read_csv(io.BytesIO(content), sep=delimiter, encoding=encoding, dtype=str)
        df.columns = df.columns.str.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Klarte ikke å lese CSV: {e}")

    total_rows = len(df)
    columns_found = list(df.columns)

    # Auto-detect format (same logic as DataManagementService)
    is_eiendom_format = "Dim1" in df.columns
    dim2_col = "Dim2(T)" if is_eiendom_format else "Dim 2(T)"

    # Build property lookup (same logic as DataManagementService)
    result = await db.execute(select(Property))
    properties = result.scalars().all()
    prop_lookup: dict[str, str] = {}
    for p in properties:
        if p.name:
            prop_lookup[p.name.lower()] = p.name
        if p.address:
            prop_lookup[p.address.lower()] = p.name or p.address

    matched_rows = 0
    unmatched_rows = 0
    matched_property_names: set[str] = set()
    sample_unmatched: list[str] = []

    has_dim2 = dim2_col in df.columns

    for _, row in df.iterrows():
        dim2_t = row.get(dim2_col) if has_dim2 else None
        prop_name = None

        if dim2_t and not pd.isna(dim2_t):
            clean_name = str(dim2_t).split(",")[0].strip().lower()
            prop_name = prop_lookup.get(clean_name)

            if not prop_name:
                for p_key, p_name in prop_lookup.items():
                    if p_key in clean_name or clean_name in p_key:
                        prop_name = p_name
                        break

        if prop_name:
            matched_rows += 1
            matched_property_names.add(prop_name)
        else:
            unmatched_rows += 1
            raw_val = str(dim2_t) if (dim2_t and not pd.isna(dim2_t)) else "(tom)"
            if len(sample_unmatched) < 20 and raw_val not in sample_unmatched:
                sample_unmatched.append(raw_val)

    return {
        "total_rows": total_rows,
        "matched_rows": matched_rows,
        "unmatched_rows": unmatched_rows,
        "match_rate_pct": round(matched_rows / total_rows * 100, 1) if total_rows else 0,
        "matched_properties": sorted(matched_property_names),
        "sample_unmatched": sample_unmatched,
        "columns_found": columns_found,
    }


@router.post("/financial-csv")
async def import_financial_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Import a Xledger/Visma CSV file into the gl_transactions table.
    Unmatched rows are skipped (not assigned to a random property).
    """
    content = await file.read()
    result = await DataManagementService.import_financial_csv(db, content)

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    return result


@router.post("/master-csv")
async def import_master_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Import property master data from totalny.txt / Eie1212 format.
    Updates lokalisering_id, region, total_area, municipality, and external_data on properties.
    """
    content = await file.read()
    result = await DataManagementService.import_property_master_csv(db, content)

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    return result


@router.post("/clear")
async def clear_economic_data(db: AsyncSession = Depends(get_db)):
    """
    Clear all economic data tables: gl_transactions, budget, text_content,
    socioeconomic_data, and related fields in properties/contracts.
    """
    result = await DataManagementService.clear_all_economic_data(db)

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])

    return result


# ---------------------------------------------------------------------------
# Koststed-mapping import (UTF-8 CSV, ~572 rader, rask)
# ---------------------------------------------------------------------------
@router.post("/koststed-mapping")
async def import_koststed_mapping(
    file: UploadFile = File(..., description="koststed_eiendom_mapping.csv (UTF-8)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Importer koststed→eiendom-mapping fra CSV.
    Kolonner: Koststed_Kode, Koststed_Navn, Region, Eksempel_Adresse
    Idempotent: sletter eksisterende rader og setter inn på nytt.
    """
    content_bytes = await file.read()
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text_content = content_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise HTTPException(status_code=400, detail="Klarte ikke decode filen (prøvde utf-8/latin-1)")

    region_map = {
        "Øst": "Øst", "ost": "Øst",
        "Sør": "Sør", "sor": "Sør",
        "Vest": "Vest",
        "Midt": "Midt-Norge",
        "Nord": "Nord",
        "Bufdir": "Bufdir",
        "7": "Ukjent", "": "Ukjent",
    }

    rows_parsed: list[dict] = []
    reader = csv.DictReader(io.StringIO(text_content))
    for row in reader:
        kode = (row.get("Koststed_Kode") or "").strip()
        if not kode:
            continue
        raw_region = (row.get("Region") or "").strip()
        rows_parsed.append({
            "kode": kode,
            "navn": (row.get("Koststed_Navn") or "").strip() or None,
            "region": region_map.get(raw_region, raw_region) or "Ukjent",
            "adresse": (row.get("Eksempel_Adresse") or "").strip() or None,
        })

    if not rows_parsed:
        raise HTTPException(status_code=400, detail="Ingen gyldige rader funnet i CSV")

    await db.execute(text("DELETE FROM koststed_mapping"))
    inserted = 0
    errors = 0
    for r in rows_parsed:
        try:
            await db.execute(
                text("""
                    INSERT INTO koststed_mapping (koststed_kode, koststed_navn, region, eksempel_adresse)
                    VALUES (:kode, :navn, :region, :adresse)
                    ON CONFLICT (koststed_kode) DO UPDATE
                      SET koststed_navn = EXCLUDED.koststed_navn,
                          region = EXCLUDED.region,
                          eksempel_adresse = EXCLUDED.eksempel_adresse
                """),
                r,
            )
            inserted += 1
        except Exception as e:
            logger.warning("koststed_mapping insert feil %s: %s", r["kode"], e)
            errors += 1

    await db.commit()

    # Region-fordeling
    result = await db.execute(
        text("SELECT region, COUNT(*) as n FROM koststed_mapping GROUP BY region ORDER BY n DESC")
    )
    region_dist = [{"region": row[0], "count": row[1]} for row in result.fetchall()]

    return {
        "status": "ok",
        "parsed": len(rows_parsed),
        "inserted": inserted,
        "errors": errors,
        "region_fordeling": region_dist,
    }


# ---------------------------------------------------------------------------
# Agresso GL import — bakgrunns-jobb (136k rader, kan ta 30-120 sek)
# ---------------------------------------------------------------------------
async def _run_gl_import(content_bytes: bytes, filename: str) -> None:
    """Kjøres som BackgroundTask. Oppdaterer _gl_import_status underveis."""
    global _gl_import_status
    _gl_import_status = {"state": "running", "message": "Starter import…", "progress": 0}

    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        _gl_import_status = {"state": "error", "message": "DATABASE_URL ikke satt"}
        return

    try:
        import asyncpg
    except ImportError:
        _gl_import_status = {"state": "error", "message": "asyncpg ikke installert"}
        return

    conn_str = db_url.replace("postgresql+asyncpg://", "postgresql://")
    try:
        conn = await asyncpg.connect(conn_str, ssl="require")
    except Exception as e:
        _gl_import_status = {"state": "error", "message": f"DB-tilkobling feilet: {e}"}
        return

    try:
        # Last koststed-mapping
        km_rows = await conn.fetch("SELECT koststed_kode, property_id FROM koststed_mapping")
        koststed_map: dict[str, str | None] = {
            r["koststed_kode"]: str(r["property_id"]) if r["property_id"] else None
            for r in km_rows
        }
        _gl_import_status["message"] = f"Lastet {len(koststed_map)} koststed-mappinger. Parser CSV…"

        # Decode
        for enc in ("latin-1", "utf-8-sig", "utf-8"):
            try:
                text_content = content_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            _gl_import_status = {"state": "error", "message": "Klarte ikke decode CSV"}
            return

        batch_id = f"agresso_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_upload"
        rows_to_insert: list[dict] = []
        skipped = 0

        reader = csv.DictReader(io.StringIO(text_content))
        for i, row in enumerate(reader):
            belop = _rens_belop(row.get("Beløp", ""))
            if belop is None:
                skipped += 1
                continue

            konto = (row.get("Konto") or "").strip()
            ba_kode = (row.get("BA") or "").strip()
            dim1_kode = (row.get("Dim1") or "").strip()
            dim6_raw = (row.get("Dim6") or "").strip()
            periode = (row.get("Periode") or "").strip() or None
            ar: int | None = None
            maaned: int | None = None
            if periode and len(periode) == 6:
                try:
                    ar = int(periode[:4])
                    maaned = int(periode[4:])
                except ValueError:
                    pass

            dim6_anlegg_id = dim6_raw if (dim6_raw and konto in ANLEGG_KONTOER) else None
            dim6_ansatt_id = dim6_raw if (dim6_raw and konto not in ANLEGG_KONTOER) else None
            leverandor_navn = (row.get("Resk.nr(T)") or "").strip() or None
            is_statsbygg = bool(leverandor_navn and "statsbygg" in leverandor_navn.lower())
            property_id = koststed_map.get(dim1_kode) if dim1_kode else None

            rows_to_insert.append({
                "transaction_id": str(uuid.uuid4()),
                "batch_id": batch_id,
                "imported_by": "admin_upload",
                "source_file_ref": filename,
                "ba_kode": ba_kode or None,
                "bilagsnr": (row.get("Bilagsnr") or "").strip() or None,
                "bilagsdato": _parse_dato(row.get("Bilagsdato", "")),
                "periode": periode,
                "ar": ar,
                "maaned": maaned,
                "konto": konto or None,
                "konto_navn": (row.get("Konto(T)") or "").strip() or None,
                "av_konto": (row.get("AV") or "").strip() or None,
                "region": (row.get("Region") or "").strip() or None,
                "dim1_kode": dim1_kode or None,
                "dim1_navn": (row.get("Dim1(T)") or "").strip() or None,
                "dim2_kode": (row.get("Dim2") or "").strip() or None,
                "dim2_navn": (row.get("Dim2(T)") or "").strip() or None,
                "dim3_kode": (row.get("Dim3") or "").strip() or None,
                "dim4_kode": (row.get("Dim4") or "").strip() or None,
                "dim5_kode": (row.get("Dim5") or "").strip() or None,
                "dim6_anlegg_id": dim6_anlegg_id,
                "dim6_ansatt_id": dim6_ansatt_id,
                "dim7_kode": (row.get("Dim7") or "").strip() or None,
                "tekst": ((row.get("Tekst") or "").strip())[:500] or None,
                "belop": belop,
                "leverandor_id": (row.get("Resk.nr") or "").strip() or None,
                "leverandor_navn": leverandor_navn,
                "property_id": property_id,
                "srs_kategori": _bestem_srs_kategori(konto, ba_kode),
                "is_statsbygg": is_statsbygg,
                "created_at": datetime.datetime.now(datetime.timezone.utc),
            })

            if (i + 1) % 10000 == 0:
                _gl_import_status["message"] = f"Lest {i+1} rader…"
                _gl_import_status["progress"] = i + 1

        _gl_import_status["message"] = f"Parsed {len(rows_to_insert)} rader. Sletter eksisterende…"

        # Slett eksisterende
        await conn.execute("DELETE FROM gl_transactions")

        # Batch-insert
        COLS = [
            "transaction_id", "batch_id", "imported_by", "source_file_ref",
            "ba_kode", "bilagsnr", "bilagsdato", "periode", "ar", "maaned",
            "konto", "konto_navn", "av_konto", "region",
            "dim1_kode", "dim1_navn", "dim2_kode", "dim2_navn", "dim3_kode",
            "dim4_kode", "dim5_kode", "dim6_anlegg_id", "dim6_ansatt_id", "dim7_kode",
            "tekst", "belop", "leverandor_id", "leverandor_navn",
            "property_id", "srs_kategori", "is_statsbygg", "created_at",
        ]
        BATCH_SIZE = 1000
        inserted = 0
        insert_errors = 0

        for start in range(0, len(rows_to_insert), BATCH_SIZE):
            batch = rows_to_insert[start:start + BATCH_SIZE]
            try:
                await conn.executemany(
                    f"INSERT INTO gl_transactions ({', '.join(COLS)}) "
                    f"VALUES ({', '.join(f'${i+1}' for i in range(len(COLS)))})",
                    [tuple(r[c] for c in COLS) for r in batch],
                )
                inserted += len(batch)
            except Exception as e:
                logger.error("GL batch feil ved rad %d: %s", start, e)
                insert_errors += len(batch)

            if inserted % 20000 == 0 and inserted > 0:
                _gl_import_status["message"] = f"Satt inn {inserted} rader…"
                _gl_import_status["progress"] = inserted

        # Statistikk
        stats_row = await conn.fetchrow("""
            SELECT
              COUNT(*) as totalt,
              SUM(CASE WHEN srs_kategori='Investering' THEN 1 ELSE 0 END) as investering,
              SUM(CASE WHEN srs_kategori='Drift' THEN 1 ELSE 0 END) as drift,
              SUM(CASE WHEN srs_kategori='Gjennomstrømning' THEN 1 ELSE 0 END) as gjennomstromning,
              SUM(CASE WHEN is_statsbygg THEN 1 ELSE 0 END) as statsbygg,
              SUM(CASE WHEN property_id IS NOT NULL THEN 1 ELSE 0 END) as koblet
            FROM gl_transactions
        """)

        _gl_import_status = {
            "state": "done",
            "message": "Import fullført",
            "parsed": len(rows_to_insert),
            "skipped": skipped,
            "inserted": inserted,
            "insert_errors": insert_errors,
            "stats": {
                "totalt": stats_row["totalt"],
                "investering": stats_row["investering"],
                "drift": stats_row["drift"],
                "gjennomstromning": stats_row["gjennomstromning"],
                "statsbygg": stats_row["statsbygg"],
                "koblet_eiendom": stats_row["koblet"],
                "koblet_pct": round(100 * stats_row["koblet"] / max(stats_row["totalt"], 1)),
            },
        }

    except Exception as e:
        logger.exception("GL import feil")
        _gl_import_status = {"state": "error", "message": str(e)}
    finally:
        await conn.close()


@router.post("/agresso-gl")
async def import_agresso_gl(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Agresso GL CSV (latin-1, semikolon/komma)"),
):
    """
    Start import av Agresso GL-data (Eiendom_2020_2025_full.csv) i bakgrunnen.
    Poll GET /agresso-gl/status for fremdrift.
    Advarsel: sletter eksisterende gl_transactions FØR insert.
    """
    global _gl_import_status
    if _gl_import_status.get("state") == "running":
        raise HTTPException(status_code=409, detail="En import kjører allerede — vent til den er ferdig")

    content = await file.read()
    filename = file.filename or "agresso_upload.csv"
    _gl_import_status = {"state": "queued", "message": "Laster opp — starter snart…"}
    background_tasks.add_task(_run_gl_import, content, filename)
    return {"status": "started", "message": "Import startet i bakgrunnen. Poll /status for fremdrift."}


@router.get("/agresso-gl/status")
async def get_gl_import_status():
    """Hent status på pågående/siste GL-import."""
    return _gl_import_status


# ---------------------------------------------------------------------------
# Lønnskostnad CSV-import
# ---------------------------------------------------------------------------
@router.post("/salary-costs")
async def import_salary_costs(
    file: UploadFile = File(..., description="Innkjøpsanalyse lønnsutgifter pivot-CSV"),
    db: AsyncSession = Depends(get_db),
):
    """
    Importer lønnskostnader fra pivot-CSV.
    Kolonneheader på rad 9 (index 8). Seksjoner: Faste stillinger / Lønn vikarer / Arbeidsgiveravgift.
    Returnerer SalaryImportResult med match_rate_pct og umatchede institusjonsnavn.
    """
    try:
        from app.services.salary_import_service import SalaryImportService
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Klarte ikke å laste salary_import_service: {e}")

    content = await file.read()
    filename = file.filename or "salary_upload.csv"

    try:
        result = await SalaryImportService.import_salary_csv(db, content, filename)
    except Exception as e:
        logger.exception("salary_import feil")
        raise HTTPException(status_code=500, detail=f"Import feilet: {e}")

    return {
        "rows_parsed": result.rows_parsed,
        "rows_matched": result.rows_matched,
        "rows_unmatched": result.rows_unmatched,
        "match_rate_pct": result.match_rate_pct,
        "unmatched_names": result.unmatched_names,
    }


@router.post("/link-koststed-properties")
async def link_koststed_to_properties(db: AsyncSession = Depends(get_db)):
    """
    Kobler koststed_mapping til eiendommer via navnematch, og oppdaterer
    deretter gl_transactions.property_id fra koststed_mapping.

    Steg 1: UPDATE koststed_mapping SET property_id = ... WHERE koststed_navn ≈ properties.name
    Steg 2: UPDATE gl_transactions SET property_id = ... FROM koststed_mapping WHERE dim1_kode = koststed_kode
    """
    # Steg 1: match koststed_navn → properties.name (case-insensitive, eksakt)
    result1 = await db.execute(text("""
        UPDATE koststed_mapping km
        SET property_id = p.property_id
        FROM properties p
        WHERE LOWER(TRIM(km.koststed_navn)) = LOWER(TRIM(p.name))
          AND km.property_id IS NULL
    """))
    matched_exact = result1.rowcount

    # Steg 1b: fuzzy — trim og ignorer "senter"/"ungdomssenter" etc.
    result1b = await db.execute(text("""
        UPDATE koststed_mapping km
        SET property_id = p.property_id
        FROM properties p
        WHERE km.property_id IS NULL
          AND (
            LOWER(TRIM(p.name)) LIKE '%' || LOWER(TRIM(km.koststed_navn)) || '%'
            OR LOWER(TRIM(km.koststed_navn)) LIKE '%' || LOWER(TRIM(p.name)) || '%'
          )
    """))
    matched_fuzzy = result1b.rowcount

    await db.commit()

    # Steg 2: oppdater gl_transactions med property_id fra koststed_mapping
    result2 = await db.execute(text("""
        UPDATE gl_transactions gl
        SET property_id = km.property_id
        FROM koststed_mapping km
        WHERE gl.dim1_kode = km.koststed_kode
          AND km.property_id IS NOT NULL
          AND gl.property_id IS NULL
    """))
    gl_updated = result2.rowcount
    await db.commit()

    # Tell opp totalt antall GL med property_id etter oppdatering
    total_linked = (await db.execute(text(
        "SELECT COUNT(*) FROM gl_transactions WHERE property_id IS NOT NULL"
    ))).scalar()
    total_gl = (await db.execute(text("SELECT COUNT(*) FROM gl_transactions"))).scalar()

    return {
        "koststed_matched_exact": matched_exact,
        "koststed_matched_fuzzy": matched_fuzzy,
        "gl_transactions_updated": gl_updated,
        "gl_total": total_gl,
        "gl_linked_pct": round(total_linked / total_gl * 100, 1) if total_gl else 0,
    }


@router.post("/fix-srs-kategori")
async def fix_srs_kategori(db: AsyncSession = Depends(get_db)):
    """
    Reklassifiserer srs_kategori på eksisterende gl_transactions etter korrekt SRS 17:
    - Investering: konto 1268 + 4930–4999
    - Gjennomstrømning: ba_kode IN (H1, H2, HB, RE)
    - Drift: alt annet
    Idempotent — trygt å kjøre flere ganger.
    """
    # 1. Investering: konto 1268 og hele 4930–4999-serien
    res_inv = await db.execute(text("""
        UPDATE gl_transactions
        SET srs_kategori = 'Investering'
        WHERE (
            konto = '1268'
            OR (konto ~ '^[0-9]+$' AND konto::integer BETWEEN 4930 AND 4999)
        )
        AND ba_kode NOT IN ('H1', 'H2', 'HB', 'RE')
        AND srs_kategori != 'Investering'
    """))
    investering_updated = res_inv.rowcount

    # 2. Gjennomstrømning: ba_kode er omposteringsart
    res_gj = await db.execute(text("""
        UPDATE gl_transactions
        SET srs_kategori = 'Gjennomstrømning'
        WHERE UPPER(ba_kode) IN ('H1', 'H2', 'HB', 'RE')
        AND srs_kategori != 'Gjennomstrømning'
    """))
    gjennomstromning_updated = res_gj.rowcount

    # 3. Drift: alt annet som ikke allerede er korrekt
    res_drift = await db.execute(text("""
        UPDATE gl_transactions
        SET srs_kategori = 'Drift'
        WHERE UPPER(ba_kode) NOT IN ('H1', 'H2', 'HB', 'RE')
        AND NOT (
            konto = '1268'
            OR (konto ~ '^[0-9]+$' AND konto::integer BETWEEN 4930 AND 4999)
        )
        AND srs_kategori != 'Drift'
    """))
    drift_updated = res_drift.rowcount

    await db.commit()

    # Tellingsstatus etter oppdatering
    counts = (await db.execute(text("""
        SELECT srs_kategori, COUNT(*) as antall, SUM(belop) as total
        FROM gl_transactions
        WHERE belop > 0
        GROUP BY srs_kategori
        ORDER BY total DESC
    """))).all()

    return {
        "updated": {
            "investering": investering_updated,
            "gjennomstromning": gjennomstromning_updated,
            "drift": drift_updated,
        },
        "ny_fordeling": [
            {"kategori": r.srs_kategori, "antall": r.antall, "total": float(r.total or 0)}
            for r in counts
        ],
    }
