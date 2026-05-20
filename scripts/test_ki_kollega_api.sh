#!/usr/bin/env bash
# Test KI Kollega API mot deployt backend (ikke localhost).
# Backend krever Authorization: Bearer <token> for /api/v1/ai/* og /api/v1/search/*.
#
# Kjør fra PROSJEKTROT (BEFS_CLEAN):
#   BEFS_API_URL=http://localhost:8000 BEFS_AUTH_TOKEN=<jwt> ./scripts/test_ki_kollega_api.sh
# Fra backend/: BEFS_API_URL=... BEFS_AUTH_TOKEN=... ../scripts/test_ki_kollega_api.sh
#
# Hent token: Logg inn i appen (Vercel), åpne DevTools → Application → Cookies (eller Network
# → velg request mot API → Headers → Authorization) og kopier Bearer-tokenet.

set -e
BASE="${BEFS_API_URL:-${NEXT_PUBLIC_API_URL}}"
if [ -z "$BASE" ]; then
  echo "Sett BEFS_API_URL eller NEXT_PUBLIC_API_URL (backend-URL uten /api/v1)"
  echo "Kjør fra prosjektrot:#   BEFS_API_URL=http://localhost:8000 ./scripts/test_ki_kollega_api.sh"
  exit 1
fi

# Alle endepunkter unntatt /api/v1/health krever auth
CURL_AUTH=()
if [ -n "$BEFS_AUTH_TOKEN" ]; then
  CURL_AUTH=(-H "Authorization: Bearer $BEFS_AUTH_TOKEN")
else
  echo "Advarsel: BEFS_AUTH_TOKEN er ikke satt – forespørsler mot /api/v1/ai/* og /api/v1/search/* får 401."
  echo "Hent JWT fra appen etter innlogging (DevTools → Network → Authorization header)."
  echo ""
fi

echo "=== KI Kollega API-tester mot $BASE ==="
echo ""

echo "1. App health (åpent endepunkt)"
curl -s "$BASE/api/v1/health" | python3 -m json.tool
echo ""

echo "2. KI Kollega health"
curl -s "${CURL_AUTH[@]}" "$BASE/api/v1/ai/health" | python3 -m json.tool
echo ""

echo "3. Global søk (kontraktnavn/eiendom)"
curl -s "${CURL_AUTH[@]}" "$BASE/api/v1/search/global?q=Nybøvegen" | python3 -m json.tool
echo ""

echo "4. Chat (uten sidekontekst)"
curl -s -X POST "${CURL_AUTH[@]}" "$BASE/api/v1/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hei"}' | python3 -m json.tool
echo ""

if [ -n "$CONTRACT_ID" ]; then
  echo "5. Chat med sidekontekst (contract)"
  curl -s -X POST "${CURL_AUTH[@]}" "$BASE/api/v1/ai/chat" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Hva viser denne kontrakten?\", \"context\": {\"entity_type\": \"contract\", \"entity_id\": \"$CONTRACT_ID\"}}" | python3 -m json.tool
else
  echo "5. Hoppet over (sett CONTRACT_ID for å teste sidekontekst)"
fi

echo ""
echo "Ferdig."
