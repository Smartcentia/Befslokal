#!/usr/bin/env python3
"""
Kjør budsjett-prediksjon (xgb70 + xgb50) og lønnsprediksjon 2027 mot gjeldende DATABASE_URL.

  cd backend && BEFS_DATABASE_TIER=staging python3 scripts/run_prediksjon_2027_pipeline.py
  cd backend && ... python3 scripts/run_prediksjon_2027_pipeline.py --salary-only

Krever BEFS_DATABASE_TIER=staging eller BEFS_ALLOW_PROD_WRITE=1, med mindre BEFS_SKIP_GUARD=1.
Lønnsprediksjon bruker historikk tom (target_year - 2) = 2025 i SalaryPredictionService.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

_VENV_PY = BACKEND_ROOT / ".venv" / "bin" / "python"


def _python_exe() -> str:
    if _VENV_PY.is_file():
        return str(_VENV_PY)
    return sys.executable


def _reexec_with_venv_if_old_python() -> None:
    """prediction_service bruker PEP604-annotasjoner som krever Python 3.10+."""
    if sys.version_info >= (3, 10):
        return
    if not _VENV_PY.is_file():
        print(
            "FEIL: Python 3.10+ kreves for lønnsprediksjon; opprett backend/.venv "
            "(python3 -m venv .venv && pip install -r requirements.txt)."
        )
        sys.exit(1)
    os.execv(str(_VENV_PY), [str(_VENV_PY), str(Path(__file__).resolve()), *sys.argv[1:]])


def _writes_ok() -> bool:
    return os.environ.get("BEFS_DATABASE_TIER", "").lower() == "staging" or (
        os.environ.get("BEFS_ALLOW_PROD_WRITE", "").strip() == "1"
    )


async def _salary_2027() -> None:
    from app.db.session import SessionLocal
    from app.services.salary_prediction_service import SalaryPredictionService

    async with SessionLocal() as db:
        out = await SalaryPredictionService.predict_all_properties(
            db,
            target_year=2027,
            history_from=2020,
            inflation=0.045,
        )
        print("Lønnsprediksjon:", out)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Prediksjon 2027: budsjett + lønn")
    ap.add_argument(
        "--salary-only",
        action="store_true",
        help="Kun lønnsprediksjon (hopp over budsjett xgb70/xgb50)",
    )
    args = ap.parse_args()

    _reexec_with_venv_if_old_python()

    if not os.environ.get("BEFS_SKIP_GUARD") and not _writes_ok():
        print(
            "Avbrutt: sett BEFS_DATABASE_TIER=staging eller BEFS_ALLOW_PROD_WRITE=1, "
            "eller BEFS_SKIP_GUARD=1 med forsiktighet."
        )
        sys.exit(1)

    if not args.salary_only:
        for tag in ("xgb70", "xgb50"):
            env = {**os.environ, "PREDICTION_DATA_SOURCE_TAG": tag}
            print(f"\n=== Budsjett prediksjon scenario={tag} ===")
            subprocess.check_call(
                [_python_exe(), str(BACKEND_ROOT / "scripts" / "run_prediction.py")],
                cwd=str(BACKEND_ROOT),
                env=env,
            )

    print("\n=== Lønnsprediksjon 2027 ===")
    asyncio.run(_salary_2027())
    print("\nFerdig.")


if __name__ == "__main__":
    main()
