"""
Skriv prediksjon 2027 Excel til disk — samme workbook som API:
  GET /api/v1/financials/prediksjon-2027/excel  GET /api/v1/financials/prediksjon-2027/export.xlsx

Ark: Sammendrag, Alle eiendommer, Forklaring, Eiendom_kategori, GL_konto, GL_bilag.

Kjør fra backend med DATABASE_URL (f.eks. i .env):
  cd backend && python scripts/export_prediksjon_2027_xlsx.py

Valgfri utdatafil:
  python scripts/export_prediksjon_2027_xlsx.py -o ../tools/prediksjon-excel-viewer-pakke/prediksjon_2027_export.xlsx
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

if __name__ == "__main__":
    _backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _backend not in sys.path:
        sys.path.insert(0, _backend)

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except Exception:
    pass

import app.db.base  # noqa: F401 — registrer modeller

from app.api.v1.financials import _build_prediksjon_2027_excel_workbook
from app.db.session import SessionLocal


async def run(out_path: str) -> int:
    async with SessionLocal() as session:
        buf = await _build_prediksjon_2027_excel_workbook(session)
        data = buf.getvalue()
    out_abs = os.path.abspath(out_path)
    d = os.path.dirname(out_abs)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(out_abs, "wb") as f:
        f.write(data)
    print(f"Skrev {len(data)} bytes til {out_abs}")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Eksporter prediksjon 2027 Excel (full workbook som API)")
    p.add_argument(
        "-o",
        "--output",
        default=os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "tools",
            "prediksjon-excel-viewer-pakke",
            "prediksjon_2027_export.xlsx",
        ),
        help="Utdatafil (.xlsx)",
    )
    args = p.parse_args()
    code = asyncio.run(run(args.output))
    raise SystemExit(code)


if __name__ == "__main__":
    main()
