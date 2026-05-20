#!/usr/bin/env python3
"""
Kjør verifikasjon + master/koststed-rapporter (etter dataopprydding på staging).

  cd backend && BEFS_DATABASE_TIER=staging python3 scripts/run_prediction_data_validation.py \\
    --master /path/Master_enheter_register.xlsx

  --require-staging  krever BEFS_DATABASE_TIER=staging eller BEFS_ALLOW_PROD_WRITE=1 (via verify_db_target).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = BACKEND_ROOT / "scripts"
PY = sys.executable


def main() -> None:
    ap = argparse.ArgumentParser(description="Valideringspakke for prediksjonsgrunnlag")
    ap.add_argument("--master", type=Path, required=True, help="Master_enheter_register.xlsx")
    ap.add_argument(
        "--compare-csv",
        type=Path,
        default=Path("/tmp/befs_master_vs_salary.csv"),
    )
    ap.add_argument(
        "--audit-csv",
        type=Path,
        default=Path("/tmp/befs_koststed_audit.csv"),
    )
    ap.add_argument(
        "--require-staging",
        action="store_true",
        help="Kall verify_db_target med --require-staging",
    )
    args = ap.parse_args()

    vcmd = [PY, str(SCRIPTS / "verify_db_target.py")]
    if args.require_staging:
        vcmd.append("--require-staging")
    r0 = subprocess.run(vcmd, cwd=str(BACKEND_ROOT))
    if r0.returncode != 0:
        sys.exit(r0.returncode)

    r1 = subprocess.run(
        [
            PY,
            str(SCRIPTS / "compare_master_enheter_db_costs.py"),
            "--master",
            str(args.master),
            "--csv",
            str(args.compare_csv),
        ],
        cwd=str(BACKEND_ROOT),
    )
    r2 = subprocess.run(
        [
            PY,
            str(SCRIPTS / "audit_koststed_unit_erp_mismatch.py"),
            "--master",
            str(args.master),
            "--csv",
            str(args.audit_csv),
        ],
        cwd=str(BACKEND_ROOT),
    )

    print("\n--- Filer ---")
    print("compare:", args.compare_csv)
    print("audit: ", args.audit_csv)
    if r1.returncode != 0 or r2.returncode != 0:
        sys.exit(1 if (r1.returncode or r2.returncode) else 0)
    print("\nOK — alle delskript returnerte 0.")


if __name__ == "__main__":
    main()
