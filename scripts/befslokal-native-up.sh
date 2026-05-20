#!/usr/bin/env bash
# Befslokal uten Docker – Postgres (conda), Ollama, backend, frontend
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PATH="$HOME/miniconda3/bin:/Applications/Ollama.app/Contents/Resources:$PATH"
PGDATA="${PGDATA:-$HOME/befslokal-pgdata}"

echo "=== Postgres ==="
if ! pg_isready -h localhost -q 2>/dev/null; then
  [ -f "$PGDATA/PG_VERSION" ] || initdb -D "$PGDATA" -U postgres --auth-host=trust --auth-local=trust
  pg_ctl -D "$PGDATA" -l "$PGDATA/server.log" start
  sleep 2
fi
psql -h localhost -U postgres -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='eiendom'" | grep -q 1 \
  || psql -h localhost -U postgres -d postgres -c "CREATE DATABASE eiendom;"
psql -h localhost -U postgres -d eiendom -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true

echo "=== Ollama ==="
open -a Ollama 2>/dev/null || true
sleep 3
ollama list | grep -q mistral || ollama pull mistral
ollama list | grep -q nomic-embed-text || ollama pull nomic-embed-text

echo "=== Backend ==="
cd "$ROOT/backend"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
alembic upgrade head
python scripts/befslokal_seed.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
echo $! > "$ROOT/.befslokal-backend.pid"

echo "=== Frontend ==="
cd "$ROOT/frontend"
[ -d node_modules ] || npm ci
npm run dev &
echo $! > "$ROOT/.befslokal-frontend.pid"

echo ""
echo "Befslokal kjører (native):"
echo "  http://localhost:3000  (admin@befslokal.no / befslokal123)"
echo "  http://localhost:8000/api/v1/health"
