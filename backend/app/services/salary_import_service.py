"""
Lønnskostnad CSV-import service.

Leser pivot-CSV fra Innkjøpsanalyse 2026 lønnsutgifter.
CSV-format: rad 9 (index 8) er kolonneheader.
Seksjoner: "Faste stillinger", "Lønn vikarer", "Arbeidsgiveravgift".
Matcher institusjons-/avdelingsnavn mot properties.name / properties.department_name.
Upsert på (property_id, year).
"""
from __future__ import annotations

import io
import logging
import datetime
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

YEAR_COLS = [str(y) for y in range(2020, 2027)]  # 2020–2026

SECTION_MARKERS = {
    "faste stillinger": "faste_stillinger",
    "lønn vikarer": "vikarer",
    "arbeidsgiveravgift": "arbeidsgiveravgift",
}

SKIP_PREFIXES = ("region ",)
SKIP_EXACT = {"bufetat", "totalsum", ""}


@dataclass
class SalaryImportResult:
    rows_parsed: int = 0
    rows_matched: int = 0
    rows_unmatched: int = 0
    match_rate_pct: float = 0.0
    unmatched_names: list[str] = field(default_factory=list)


def _parse_norwegian_number(raw: str) -> Decimal:
    """Parser norsk tallformat: fjerner \xa0 og mellomrom, håndterer minus."""
    if not raw or not str(raw).strip():
        return Decimal(0)
    s = str(raw).replace("\xa0", "").replace(" ", "").replace("\u2009", "")
    s = s.strip()
    if not s or s in ("-", "—"):
        return Decimal(0)
    # Håndter komma som desimalskilletegn (norsk)
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    elif "," in s and "." in s:
        # Tusen-skilletegn er punktum, desimal er komma: 1.234,56
        s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except Exception:
        return Decimal(0)


def _should_skip(first_col: str) -> bool:
    """True dersom raden skal hoppes over."""
    stripped = str(first_col).strip()
    lower = stripped.lower()
    if not stripped:
        return True
    if lower in SKIP_EXACT:
        return True
    for prefix in SKIP_PREFIXES:
        if lower.startswith(prefix):
            return True
    return False


class SalaryImportService:

    @staticmethod
    async def import_salary_csv(
        db: AsyncSession,
        content: bytes,
        filename: str = "salary_upload.csv",
    ) -> SalaryImportResult:
        result = SalaryImportResult()

        # --- 1. Decode ---
        text_content: str | None = None
        for enc in ("utf-8-sig", "windows-1252", "latin-1", "utf-8"):
            try:
                text_content = content.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if text_content is None:
            text_content = content.decode("utf-8", errors="replace")

        # Auto-detect delimiter
        sample = text_content[:2000]
        delimiter = ";" if sample.count(";") > sample.count(",") else ","

        # --- 2. Parse CSV: header on row 8 (index 7, "Radetiketter, 2020, ...") ---
        try:
            df = pd.read_csv(
                io.StringIO(text_content),
                sep=delimiter,
                header=7,
                dtype=str,
            )
        except Exception as e:
            logger.warning("salary_import: CSV-parsefeil: %s", e)
            return result

        if df.empty or df.shape[1] < 2:
            logger.warning("salary_import: tom eller for liten CSV (%d kolonner)", df.shape[1])
            return result

        # Rename first column to "institution_name" regardless of original header
        cols = list(df.columns)
        first_col = cols[0]

        # Build year-column mapping: match column names to YEAR_COLS
        year_col_map: dict[str, str] = {}  # year str -> actual col name
        for col in cols[1:]:
            col_clean = str(col).strip()
            if col_clean in YEAR_COLS:
                year_col_map[col_clean] = col

        if not year_col_map:
            logger.warning("salary_import: ingen årskolonner funnet. Kolonner: %s", cols)
            return result

        # --- 3. Load properties for matching ---
        prop_rows = (await db.execute(text(
            "SELECT property_id::text, name, department_name FROM properties WHERE name IS NOT NULL"
        ))).fetchall()

        # Build lookup: lower(name) -> property_id
        exact_map: dict[str, str] = {}
        for row in prop_rows:
            if row[1]:
                exact_map[row[1].strip().lower()] = row[0]
            if row[2]:
                exact_map[row[2].strip().lower()] = row[0]

        def match_institution(name: str) -> Optional[str]:
            """To-pass matching: 1) eksakt, 2) substring fuzzy."""
            n = name.strip().lower()
            if n in exact_map:
                return exact_map[n]
            # Fuzzy: property_name contained in institution_name or vice versa
            for prop_name_lower, pid in exact_map.items():
                if prop_name_lower in n or n in prop_name_lower:
                    return pid
            return None

        # --- 4. Two-pass scan: detect sections and collect values ---
        # aggregated[institution_name][year] = {faste, vikarer, aga}
        aggregated: dict[str, dict[str, dict[str, Decimal]]] = {}
        current_section: Optional[str] = None  # 'faste_stillinger' | 'vikarer' | 'arbeidsgiveravgift'

        for _, row_series in df.iterrows():
            inst_raw = str(row_series.get(first_col, "") or "").strip()
            lower_inst = inst_raw.lower().strip()

            # Section marker detection
            if lower_inst in SECTION_MARKERS:
                current_section = SECTION_MARKERS[lower_inst]
                continue

            if current_section is None:
                continue

            if _should_skip(inst_raw):
                continue

            # Data row
            inst_key = inst_raw  # preserve original for audit
            if inst_key not in aggregated:
                aggregated[inst_key] = {}

            for year_str, col_name in year_col_map.items():
                raw_val = str(row_series.get(col_name, "") or "")
                amount = _parse_norwegian_number(raw_val)
                if amount == 0:
                    continue
                if year_str not in aggregated[inst_key]:
                    aggregated[inst_key][year_str] = {
                        "faste_stillinger": Decimal(0),
                        "vikarer": Decimal(0),
                        "arbeidsgiveravgift": Decimal(0),
                    }
                aggregated[inst_key][year_str][current_section] += amount

        result.rows_parsed = sum(len(years) for years in aggregated.values())
        if result.rows_parsed == 0:
            logger.warning("salary_import: ingen datarader etter parsing")
            return result

        # --- 5. Match institutions and upsert ---
        batch_id = f"salary_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}_{filename[:40]}"
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        unmatched_set: set[str] = set()

        for inst_name, year_data in aggregated.items():
            property_id = match_institution(inst_name)
            if property_id is None:
                unmatched_set.add(inst_name)

            for year_str, vals in year_data.items():
                year_int = int(year_str)

                if property_id is not None:
                    # Upsert: ON CONFLICT (property_id, year) DO UPDATE
                    await db.execute(text("""
                        INSERT INTO salary_costs
                            (salary_cost_id, property_id, year,
                             faste_stillinger, vikarer, arbeidsgiveravgift,
                             institution_name_raw, import_batch_id, imported_at)
                        VALUES
                            (:id, :property_id, :year,
                             :faste, :vikarer, :aga,
                             :inst_name, :batch_id, :imported_at)
                        ON CONFLICT (property_id, year) DO UPDATE
                          SET faste_stillinger    = EXCLUDED.faste_stillinger,
                              vikarer             = EXCLUDED.vikarer,
                              arbeidsgiveravgift  = EXCLUDED.arbeidsgiveravgift,
                              institution_name_raw = EXCLUDED.institution_name_raw,
                              import_batch_id     = EXCLUDED.import_batch_id,
                              imported_at         = EXCLUDED.imported_at
                    """), {
                        "id": str(uuid.uuid4()),
                        "property_id": property_id,
                        "year": year_int,
                        "faste": float(vals["faste_stillinger"]),
                        "vikarer": float(vals["vikarer"]),
                        "aga": float(vals["arbeidsgiveravgift"]),
                        "inst_name": inst_name,
                        "batch_id": batch_id,
                        "imported_at": now_utc,
                    })
                    result.rows_matched += 1
                else:
                    # Store unmatched row with property_id = NULL (audit)
                    await db.execute(text("""
                        INSERT INTO salary_costs
                            (salary_cost_id, property_id, year,
                             faste_stillinger, vikarer, arbeidsgiveravgift,
                             institution_name_raw, import_batch_id, imported_at)
                        VALUES
                            (:id, NULL, :year,
                             :faste, :vikarer, :aga,
                             :inst_name, :batch_id, :imported_at)
                    """), {
                        "id": str(uuid.uuid4()),
                        "year": year_int,
                        "faste": float(vals["faste_stillinger"]),
                        "vikarer": float(vals["vikarer"]),
                        "aga": float(vals["arbeidsgiveravgift"]),
                        "inst_name": inst_name,
                        "batch_id": batch_id,
                        "imported_at": now_utc,
                    })
                    result.rows_unmatched += 1

        await db.commit()

        result.unmatched_names = sorted(unmatched_set)
        total = result.rows_matched + result.rows_unmatched
        result.match_rate_pct = round(result.rows_matched / total * 100, 1) if total > 0 else 0.0

        logger.debug(
            "salary_import: parsed=%d matched=%d unmatched=%d rate=%.1f%%",
            result.rows_parsed,
            result.rows_matched,
            result.rows_unmatched,
            result.match_rate_pct,
        )
        return result
