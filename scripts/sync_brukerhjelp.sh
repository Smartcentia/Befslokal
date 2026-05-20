#!/bin/bash
# Synkroniser docs/BRUKERHJELP.md til backend/docs/ for deploy.
# Kjør dette når du oppdaterer brukerhjelpen, f.eks. før deploy.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/docs/BRUKERHJELP.md"
DST="$ROOT/backend/docs/BRUKERHJELP.md"
if [ ! -f "$SRC" ]; then
  echo "❌ Kildefil mangler: $SRC"
  exit 1
fi
cp "$SRC" "$DST"
echo "✅ Synkronisert BRUKERHJELP.md til backend/docs/"