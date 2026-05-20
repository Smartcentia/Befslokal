#!/usr/bin/env python3
"""
Eksporter database-relasjoner som Mermaid erDiagram (stdout eller --out).

Krever DATABASE_URL (f.eks. backend/.env). Bruker synkron SQLAlchemy-engine;
asyncpg-delen i URL strippes.

Eksempel:
  cd backend && python scripts/export_schema_mermaid.py
  python scripts/export_schema_mermaid.py --out /tmp/schema.mmd
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))
os.chdir(_backend)

try:
    from dotenv import load_dotenv

    load_dotenv(_backend / ".env", override=False)
    load_dotenv(_backend.parent / ".env", override=False)
except Exception:
    pass

from sqlalchemy import create_engine, inspect  # noqa: E402

from app.services.governance.schema_graph import build_schema_graph, to_mermaid_er  # noqa: E402


def _sync_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("DATABASE_URL er ikke satt.", file=sys.stderr)
        sys.exit(1)
    url = url.strip().strip('"').strip("'")
    if "+asyncpg" in url:
        url = url.replace("+asyncpg", "")
    if "?" in url:
        url = url.split("?", 1)[0]
    return url


def main() -> None:
    parser = argparse.ArgumentParser(description="Eksporter DB-skjema som Mermaid erDiagram")
    parser.add_argument("--out", type=Path, default=None, help="Fil å skrive til (default: stdout)")
    args = parser.parse_args()

    db_url = _sync_url()
    engine = create_engine(db_url)
    try:
        inspector = inspect(engine)
        data = build_schema_graph(inspector)
        text = to_mermaid_er(data)
    finally:
        engine.dispose()

    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"Skrev {args.out}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
