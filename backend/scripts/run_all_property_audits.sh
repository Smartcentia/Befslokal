#!/usr/bin/env bash
# Kjør alle eiendomsrevisjonsskript etter hverandre (forgrunn – ikke bakgrunn).
# Bruk: fra backend/: ./scripts/run_all_property_audits.sh
# Med Railway DB: fra repo-rot: railway run bash backend/scripts/run_all_property_audits.sh

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BACKEND"
export PYTHONPATH=.

PY="${BACKEND}/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="python3"
fi

echo "==> audit_properties_quality_bufdir.py"
"$PY" scripts/audit_properties_quality_bufdir.py

echo "==> audit_properties_full.py"
"$PY" scripts/audit_properties_full.py

echo "Ferdig. Rapporter under backend/data/"
