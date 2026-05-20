#!/usr/bin/env python3
"""
Revisjon av gl_transactions 2020–2025:
- Kobling til eiendom (mangler, avvik department_code)
- Mulige dobbeltføringer (faktura/beløp/periode, kryss-eiendom)
- 2025: sammenligning GL vs property_annual_costs (aggregerte felt)

Kjør fra repo-root eller backend/:
  cd backend && python -m scripts.audit_gl_properties_2020_2025 [--output rapport.md]
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_env = Path(__file__).resolve().parents[1] / ".env"
if _env.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
    except ImportError:
        pass

from sqlalchemy import text

from app.db.session import SessionLocal


YEAR_MIN, YEAR_MAX = 2020, 2025


def _md_table(headers: List[str], rows: List[Tuple[Any, ...]], max_rows: int = 50) -> str:
    lines = ["| " + " | ".join(str(h) for h in headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows[:max_rows]:
        lines.append("| " + " | ".join(str(x) if x is not None else "" for x in r) + " |")
    if len(rows) > max_rows:
        lines.append(f"\n*(Viser {max_rows} av {len(rows)} rader)*")
    return "\n".join(lines)


async def run_audit() -> str:
    sections: List[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sections.append(f"# Revisjonsrapport: GL-transaksjoner {YEAR_MIN}–{YEAR_MAX}\n")
    sections.append(f"*Generert: {now}*\n")

    print("Kobler til database og kjører analyser …", file=sys.stderr)

    async with SessionLocal() as db:
        # --- 1. Grunnleggende volum ---
        r = await db.execute(
            text(
                """
            SELECT
              COALESCE(year::text, 'NULL') AS yr,
              COUNT(*) AS n,
              COUNT(*) FILTER (WHERE property_id IS NULL) AS null_prop,
              ROUND(100.0 * COUNT(*) FILTER (WHERE property_id IS NULL) / NULLIF(COUNT(*), 0), 2) AS pct_null,
              COUNT(*) FILTER (WHERE is_synthetic) AS synthetic_n,
              COUNT(DISTINCT property_id) FILTER (WHERE property_id IS NOT NULL) AS distinct_props,
              ROUND(SUM(amount)::numeric, 2) AS sum_amount,
              COUNT(DISTINCT data_source) AS n_sources,
              COUNT(DISTINCT source_system) AS n_systems
            FROM gl_transactions
            WHERE year IS NULL OR (year >= :y0 AND year <= :y1)
            GROUP BY year
            ORDER BY year NULLS LAST
            """
            ),
            {"y0": YEAR_MIN, "y1": YEAR_MAX},
        )
        per_year = r.fetchall()
        sections.append("## 1. Volum per år (inkl. rader uten år utenfor filter)\n")
        sections.append(
            _md_table(
                ["year", "rows", "null_property_id", "pct_null%", "synthetic", "distinct_props", "sum_amount", "distinct_data_source", "distinct_source_system"],
                per_year,
                max_rows=30,
            )
        )

        # Only target years explicitly
        r = await db.execute(
            text(
                """
            SELECT COUNT(*) FROM gl_transactions
            WHERE year >= :y0 AND year <= :y1
            """
            ),
            {"y0": YEAR_MIN, "y1": YEAR_MAX},
        )
        total_filtered = r.scalar() or 0
        sections.append(f"\n**Totalt rader med year i [{YEAR_MIN},{YEAR_MAX}]:** {total_filtered:,}\n")

        r = await db.execute(
            text(
                """
            SELECT COALESCE(data_source, '(tom)'), COALESCE(source_system, '(tom)'), COUNT(*)
            FROM gl_transactions
            WHERE year >= :y0 AND year <= :y1
            GROUP BY 1, 2
            ORDER BY COUNT(*) DESC
            LIMIT 25
            """
            ),
            {"y0": YEAR_MIN, "y1": YEAR_MAX},
        )
        sections.append("\n## 2. Topp kilder (data_source / source_system)\n")
        sections.append(_md_table(["data_source", "source_system", "rows"], r.fetchall(), max_rows=30))

        # --- 3. Manglende eiendom ---
        r = await db.execute(
            text(
                """
            SELECT year, COUNT(*) AS n,
              STRING_AGG(DISTINCT LEFT(COALESCE(department_name,''), 60), ' | ') FILTER (WHERE department_name IS NOT NULL) AS sample_depts
            FROM gl_transactions
            WHERE year >= :y0 AND year <= :y1 AND property_id IS NULL
            GROUP BY year
            ORDER BY year
            """
            ),
            {"y0": YEAR_MIN, "y1": YEAR_MAX},
        )
        null_by_year = r.fetchall()
        sections.append("\n## 3. Rader uten property_id (per år)\n")
        if null_by_year:
            sections.append(_md_table(["year", "count", "sample_department_names"], null_by_year, max_rows=20))
        else:
            sections.append("*Ingen rader uten property_id i perioden.*\n")

        # --- 4. Avvik: GL.department_code vs properties.department_code ---
        r = await db.execute(
            text(
                """
            SELECT g.year, COUNT(*) AS mismatch_n
            FROM gl_transactions g
            INNER JOIN properties p ON g.property_id = p.property_id
            WHERE g.year >= :y0 AND g.year <= :y1
              AND g.department_code IS NOT NULL AND TRIM(g.department_code) <> ''
              AND p.department_code IS NOT NULL AND TRIM(p.department_code) <> ''
              AND TRIM(g.department_code) <> TRIM(p.department_code)
            GROUP BY g.year
            ORDER BY g.year
            """
            ),
            {"y0": YEAR_MIN, "y1": YEAR_MAX},
        )
        mm = r.fetchall()
        sections.append("\n## 4. Mulig feilkobling: `gl.department_code` ≠ `properties.department_code`\n")
        sections.append(
            "*Når begge er satt og likevel forskjellige, kan transaksjonen være booket på annet koststed enn master for eiendommen.*\n"
        )
        if mm:
            sections.append(_md_table(["year", "rows_with_mismatch"], mm))
        else:
            sections.append("*Ingen avvik funnet (der begge felt er utfylt).*\n")

        r = await db.execute(
            text(
                """
            SELECT g.transaction_id, g.year, g.period, g.amount, g.department_code, p.department_code AS prop_dept,
              LEFT(COALESCE(p.name, p.address, ''), 50) AS prop_label
            FROM gl_transactions g
            INNER JOIN properties p ON g.property_id = p.property_id
            WHERE g.year >= :y0 AND g.year <= :y1
              AND g.department_code IS NOT NULL AND TRIM(g.department_code) <> ''
              AND p.department_code IS NOT NULL AND TRIM(p.department_code) <> ''
              AND TRIM(g.department_code) <> TRIM(p.department_code)
            ORDER BY ABS(g.amount) DESC
            LIMIT 30
            """
            ),
            {"y0": YEAR_MIN, "y1": YEAR_MAX},
        )
        samples = r.fetchall()
        if samples:
            sections.append("\n### Eksempler (topp 30 etter |beløp|)\n")
            sections.append(
                _md_table(
                    ["transaction_id", "year", "period", "amount", "gl_dept", "property_dept", "property"],
                    samples,
                    max_rows=30,
                )
            )

        # --- 5. Dobbeltføringer: samme faktura+beløp+periode på samme eiendom ---
        r = await db.execute(
            text(
                """
            SELECT year, property_id, invoice_number, period, amount, COUNT(*) AS c,
              MIN(transaction_id::text) AS sample_tid
            FROM gl_transactions
            WHERE year >= :y0 AND year <= :y1
              AND property_id IS NOT NULL
              AND invoice_number IS NOT NULL AND TRIM(invoice_number) <> ''
            GROUP BY year, property_id, invoice_number, period, amount
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC, ABS(amount) DESC
            LIMIT 40
            """
            ),
            {"y0": YEAR_MIN, "y1": YEAR_MAX},
        )
        dup_inv = r.fetchall()
        sections.append("\n## 5. Dobbeltføringer (samme `property_id`, `invoice_number`, `period`, `amount`)\n")
        if dup_inv:
            sections.append(_md_table(["year", "property_id", "invoice", "period", "amount", "count", "sample_tx"], dup_inv))
        else:
            sections.append("*Ingen grupper funnet.*\n")

        # --- 6. Samme faktura+beløp+periode på flere eiendommer (kryss-allokering) ---
        r = await db.execute(
            text(
                """
            SELECT year, invoice_number, period, amount, COUNT(DISTINCT property_id) AS n_props, COUNT(*) AS n_rows
            FROM gl_transactions
            WHERE year >= :y0 AND year <= :y1
              AND property_id IS NOT NULL
              AND invoice_number IS NOT NULL AND TRIM(invoice_number) <> ''
            GROUP BY year, invoice_number, period, amount
            HAVING COUNT(DISTINCT property_id) > 1
            ORDER BY COUNT(*) DESC
            LIMIT 30
            """
            ),
            {"y0": YEAR_MIN, "y1": YEAR_MAX},
        )
        cross = r.fetchall()
        sections.append("\n## 6. Samme faktura på flere eiendommer (`invoice_number`+`period`+`amount`)\n")
        if cross:
            sections.append(_md_table(["year", "invoice", "period", "amount", "distinct_properties", "total_rows"], cross))
        else:
            sections.append("*Ingen treff.*\n")

        # --- 7. Duplikater uten faktura: streng nøkkel ---
        r = await db.execute(
            text(
                """
            SELECT year, property_id, period, amount, account_name, supplier_name,
              LEFT(COALESCE(description,''), 40) AS descr,
              COUNT(*) AS c
            FROM gl_transactions
            WHERE year >= :y0 AND year <= :y1
              AND property_id IS NOT NULL
              AND (invoice_number IS NULL OR TRIM(invoice_number) = '')
            GROUP BY year, property_id, period, amount, account_name, supplier_name, LEFT(COALESCE(description,''), 40)
            HAVING COUNT(*) > 1
            ORDER BY COUNT(*) DESC, ABS(amount) DESC
            LIMIT 35
            """
            ),
            {"y0": YEAR_MIN, "y1": YEAR_MAX},
        )
        dup_no_inv = r.fetchall()
        sections.append(
            "\n## 7. Mulige duplikater uten fakturanummer (samme eiendom, periode, beløp, konto, leverandør, kort beskrivelse)\n"
        )
        sections.append("*Kan inkludere legitime gjentakelser (f.eks. flere like fakturaer uten nummer i import).* Vurder manuelt.\n")
        if dup_no_inv:
            sections.append(_md_table(["year", "property_id", "period", "amount", "account", "supplier", "descr_prefix", "count"], dup_no_inv))
        else:
            sections.append("*Ingen grupper.*\n")

        # --- 8. 2025: GL vs property_annual_costs ---
        sections.append("\n## 8. Avstemming 2025: `gl_transactions` vs `property_annual_costs`\n")
        sections.append(
            "For eiendommer med rad i `property_annual_costs` (år 2025) sammenlignes:\n"
            "- **gl_expense**: sum av negative `amount` (kostnader som negative tall i GL)\n"
            "- **gl_lease_pos**: sum av positive `amount` der `account_name` matcher husleie (Leie… / Husleie)\n"
            "- **pac_sum**: summen av numeriske kostnadsfelter i annual cost-raden (absoluttverdi)\n"
        )
        r = await db.execute(
            text(
                """
            WITH pac AS (
              SELECT
                property_id,
                COALESCE(ABS(kpi_adjusted_rent),0) + COALESCE(ABS(internal_maintenance),0)
                + COALESCE(ABS(common_costs),0) + COALESCE(ABS(energy_costs),0)
                + COALESCE(ABS(heating_costs),0) + COALESCE(ABS(cleaning_costs),0)
                + COALESCE(ABS(parking_rent),0) + COALESCE(ABS(caretaker_cost),0)
                + COALESCE(ABS(card_reader_cost),0) AS pac_total
              FROM property_annual_costs
              WHERE year = 2025
            ),
            gl AS (
              SELECT
                property_id,
                SUM(CASE WHEN amount < 0 THEN amount ELSE 0 END) AS expense_neg,
                SUM(CASE WHEN amount > 0 AND (
                  account_name IN ('Leie lokaler fra Statsbygg','Leie lokaler andre utleiere','Leie parkeringsplass','Leie av lager/naust/garsjer og lignende','Husleie')
                  OR (account_name ILIKE 'Leie %')
                ) THEN amount ELSE 0 END) AS lease_pos
              FROM gl_transactions
              WHERE year = 2025 AND property_id IS NOT NULL
              GROUP BY property_id
            )
            SELECT
              p.property_id,
              LEFT(COALESCE(p.name, p.address, ''), 45) AS prop,
              ROUND(pac.pac_total::numeric, 2) AS annual_costs_sum_fields,
              ROUND(COALESCE(-gl.expense_neg, 0)::numeric, 2) AS gl_cost_as_positive,
              ROUND(COALESCE(gl.lease_pos, 0)::numeric, 2) AS gl_lease_positive,
              ROUND((COALESCE(-gl.expense_neg,0) - pac.pac_total)::numeric, 2) AS diff_expense_vs_pac
            FROM pac
            INNER JOIN properties p ON p.property_id = pac.property_id
            LEFT JOIN gl gl ON gl.property_id = pac.property_id
            ORDER BY ABS(COALESCE(-gl.expense_neg,0) - pac.pac_total) DESC NULLS LAST
            LIMIT 40
            """
            )
        )
        cmp_rows = r.fetchall()
        if cmp_rows:
            sections.append("### Topp 40 avvik (størst |GL-kostnad − summerte annual fields|)\n")
            sections.append(
                _md_table(
                    ["property_id", "property", "sum_annual_cost_fields", "gl_expenses_as_positive", "gl_lease_positive", "diff"],
                    cmp_rows,
                    max_rows=40,
                )
            )
        else:
            sections.append("*Ingen overlapp: ingen `property_annual_costs` for 2025, eller ingen GL-rader 2025 for disse eiendommene.*\n")

        r = await db.execute(
            text(
                """
            SELECT COUNT(*) FROM property_annual_costs WHERE year = 2025
            """
            )
        )
        n_pac = r.scalar() or 0
        r = await db.execute(
            text(
                """
            SELECT COUNT(DISTINCT property_id) FROM gl_transactions WHERE year = 2025 AND property_id IS NOT NULL
            """
            )
        )
        n_gl = r.scalar() or 0
        sections.append(f"\n**Antall annual_cost-rader 2025:** {n_pac:,} — **Eiendommer med GL 2025:** {n_gl:,}\n")

        r = await db.execute(
            text(
                """
            SELECT
              ROUND(SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END)::numeric, 2) AS total_expense_positive,
              ROUND(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END)::numeric, 2) AS total_income_positive
            FROM gl_transactions
            WHERE year = 2025
            """
            )
        )
        tot = r.fetchone()
        if tot:
            sections.append(
                f"\n**GL 2025 (alle rader):** sum kostnader (|-negative|) = **{tot[0]}** NOK, sum positive poster = **{tot[1]}** NOK\n"
            )

        # --- 9. Orphan FK (skal ikke forekomme) ---
        r = await db.execute(
            text(
                """
            SELECT COUNT(*) FROM gl_transactions g
            WHERE g.year >= :y0 AND g.year <= :y1
              AND g.property_id IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM properties p WHERE p.property_id = g.property_id)
            """
            ),
            {"y0": YEAR_MIN, "y1": YEAR_MAX},
        )
        orphan = r.scalar() or 0
        sections.append("\n## 9. Referensiell integritet\n")
        sections.append(f"Rader med `property_id` som ikke finnes i `properties`: **{orphan}**\n")

        sections.append("\n---\n## Tolkning og anbefalinger\n")
        sections.append(
            "1. **Null property_id:** Avklar import-/koblingsregler (koststed → `unit_id_erp` / `department_code`).\n"
            "2. **Department mismatch:** Verifiser mot ERP at koststed på linjen hører til riktig eiendom.\n"
            "3. **Dobbeltføringer:** Ved `count` > 1 på samme fakturanøkkel — vurder å slette duplikater eller slå sammen kilder.\n"
            "4. **Kryss-eiendom faktura:** Sjeldent legitimt; ofte feilfordeling eller testdata.\n"
            "5. **Annual costs vs GL:** `property_annual_costs` er ikke 1:1 med kontostruktur i GL; diff er forventet, men store avvik bør undersøkes per eiendom.\n"
        )

    return "\n".join(sections)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", type=Path, help="Skriv markdown til fil")
    args = parser.parse_args()
    body = await run_audit()
    print(body)
    if args.output:
        args.output.write_text(body, encoding="utf-8")
        print(f"\n[Wrote {args.output}]", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
