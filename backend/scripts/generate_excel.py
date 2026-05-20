"""
Standalone-script for å generere prediksjon_2027_export.xlsx.
Kjør med: railway run --service BEFS1 python backend/scripts/generate_excel.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Importer alle modeller slik at SQLAlchemy-registeret er fullt
import glob as _glob, importlib as _imp, re as _re
for _p in sorted(_glob.glob(os.path.join(os.path.dirname(__file__), "../app/**/*.py"), recursive=True)):
    if "/models/" in _p and not _p.endswith("__init__.py"):
        _mod = _re.sub(r".*/(app/)", r"\1", _p).replace("/", ".").removesuffix(".py")
        try:
            _imp.import_module(_mod)
        except Exception:
            pass

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


async def main():
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        print("FEIL: DATABASE_URL er ikke satt", file=sys.stderr)
        sys.exit(1)

    engine = create_async_engine(
        db_url,
        echo=False,
        connect_args={"statement_cache_size": 0},
    )
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        from app.services.financials.prediksjon_2027_export import build_prediksjon_export_xlsx
        print("Genererer Excel (kan ta 30-60 sek)...", file=sys.stderr)
        buf = await build_prediksjon_export_xlsx(db)
        out_path = os.environ.get("EXCEL_OUT", "backend/data/prediksjon_2027_export.xlsx")
        with open(out_path, "wb") as f:
            f.write(buf.read())
        print(f"Ferdig → {out_path}", file=sys.stderr)


asyncio.run(main())
