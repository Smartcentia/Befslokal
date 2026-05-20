#!/usr/bin/env bash
# Røyktest mot kjørende backend (ikke pytest). Krever curl.
#
# Bruk:
#   export API_BASE_URL="https://din-backend.up.railway.app"
#   export BACKEND_SECRET="…"   # samme som BACKEND_SECRET / shared secret
#   export ADMIN_EMAIL="din@admin.no"  # bruker som finnes i DB med rolle ADMIN
#   ./scripts/smoke_admin_api.sh
#
# Lokalt (uvicorn):
#   API_BASE_URL="http://127.0.0.1:8000" BACKEND_SECRET="befs-super-secret-key-12345" \
#   ADMIN_EMAIL="system@befs.no" ./scripts/smoke_admin_api.sh

set -euo pipefail

API_BASE_URL="${API_BASE_URL:-}"
BACKEND_SECRET="${BACKEND_SECRET:-}"
ADMIN_EMAIL="${ADMIN_EMAIL:-}"

if [[ -z "$API_BASE_URL" || -z "$BACKEND_SECRET" || -z "$ADMIN_EMAIL" ]]; then
  echo "Sett API_BASE_URL, BACKEND_SECRET og ADMIN_EMAIL" >&2
  exit 1
fi

BASE="${API_BASE_URL%/}"

echo "GET ${BASE}/api/v1/health"
curl -sfS "${BASE}/api/v1/health" | head -c 200 || true
echo ""

echo "GET ${BASE}/api/v1/admin/stats/system (Bearer + X-User-Email)"
curl -sfS -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer ${BACKEND_SECRET}" \
  -H "X-User-Email: ${ADMIN_EMAIL}" \
  "${BASE}/api/v1/admin/stats/system"

echo "GET ${BASE}/api/v1/admin/evolution/tools"
curl -sfS -o /dev/null -w "%{http_code}\n" \
  -H "Authorization: Bearer ${BACKEND_SECRET}" \
  -H "X-User-Email: ${ADMIN_EMAIL}" \
  "${BASE}/api/v1/admin/evolution/tools"

echo "Ferdig (forvent 200 for admin-kall dersom bruker er ADMIN)."
