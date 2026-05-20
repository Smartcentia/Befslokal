#!/usr/bin/env bash
# Befslokal – start hele den lokale stacken
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Befslokal: bygger og starter tjenester ==="
docker compose up -d --build

echo "Venter på backend..."
for i in $(seq 1 60); do
  if curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; then
    echo "Backend er oppe."
    break
  fi
  sleep 2
  if [ "$i" -eq 60 ]; then
    echo "Backend svarte ikke i tide. Sjekk: docker compose logs backend"
    exit 1
  fi
done

echo ""
echo "=== Befslokal kjører ==="
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000/api/v1/health"
echo "  Ollama:    http://localhost:11434"
echo "  Postgres:  localhost:5432 (bruker postgres / postgres, db eiendom)"
echo ""
echo "  Innlogging: admin@befslokal.no / befslokal123"
echo "  (eller admin@bufdir.no / test123 hvis seed_users har kjørt)"
echo ""
echo "Første oppstart kan ta flere minutter (Mistral-nedlasting)."
