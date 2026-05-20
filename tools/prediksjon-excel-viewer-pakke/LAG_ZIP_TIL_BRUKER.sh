#!/usr/bin/env bash
# Kjør fra denne mappens forelder (tools/), eller juster stier.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
# Standard leveranse: Prediksjon 2027 Excel-viewer (samme innhold, tydelig navn)
OUT="${1:-${ROOT}/../BEFS-Prediksjon2027-Excel.zip}"
(
 cd "$ROOT/.."
  zip -r "$OUT" "$(basename "$ROOT")" -x "*.DS_Store" -x "*/.DS_Store"
)
echo "Opprettet: $OUT"
echo "Send denne ZIP-filen til brukeren. Brukeren pakker ut og åpner index.html."
