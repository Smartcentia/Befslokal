#!/usr/bin/env bash
# Kjør migrasjoner og seed inne i backend-containeren
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Alembic migrasjoner..."
docker compose exec -T backend alembic upgrade head

echo "Befslokal admin-bruker..."
docker compose exec -T backend python scripts/befslokal_seed.py

echo "Valgfritt: flere testbrukere (admin@bufdir.no / test123)..."
docker compose exec -T backend python scripts/seed_users_orm.py 2>/dev/null || true
docker compose exec -T backend python scripts/set_user_passwords.py 2>/dev/null || true

echo "Database initialisert."
