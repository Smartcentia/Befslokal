#!/usr/bin/env python3
"""
Sjekkliste før produksjons-cutover (ingen DB-endring — kun utskrift).

Kjør etter at samme steg er verifisert på staging:
  1. Ta backup / snapshot av produksjons-Postgres.
  2. BEFS_ALLOW_PROD_WRITE=1 (ikke bruk staging-flagg i prod).
  3. sync_koststed_from_unit_erp.py (ev. all-numeric etter QA).
  4. import_salary_csv med --delete-batch-before --replace --master-xlsx ...
  5. run_prediction_data_validation.py mot prod (uten --require-staging om du kun bruker ALLOW_PROD_WRITE).
  6. run_prediksjon_2027_pipeline.py
"""

from __future__ import annotations

STEPS = """
Produksjons-cutover — manuell sjekkliste
=========================================

[ ] 1. Backup: pg_dump / Railway snapshot / Supabase point-in-time
[ ] 2. sync_koststed: python3 scripts/sync_koststed_from_unit_erp.py --master ... --mode master-only
 (ev. --mode all-numeric etter forretnings-OK)
[ ] 3. Lønn: python -m app.scripts.import_salary_csv /sti/lonn.csv --replace --master-xlsx ... \\
      --delete-batch-before
      Miljø: BEFS_ALLOW_PROD_WRITE=1
[ ] 4. Valider: python3 scripts/run_prediction_data_validation.py --master ...
[ ] 5. Prediksjon: BEFS_ALLOW_PROD_WRITE=1 python3 scripts/run_prediksjon_2027_pipeline.py
[ ] 6. Verifiser API/Excel: /financials/prediksjon-2027 og excel-eksport

Viktig: Ikke sett BEFS_DATABASE_TIER=staging i produksjon; bruk BEFS_ALLOW_PROD_WRITE=1 bevisst.
"""


def main() -> None:
    print(STEPS)


if __name__ == "__main__":
    main()
