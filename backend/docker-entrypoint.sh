#!/bin/sh
set -e

echo "Befslokal backend starter..."

if [ -n "${DATABASE_URL}" ]; then
  echo "Kjører Alembic migrasjoner..."
  alembic upgrade head || echo "Advarsel: migrasjon feilet – fortsetter oppstart"

  echo "Seeder lokal admin..."
  python scripts/befslokal_seed.py || echo "Advarsel: seed feilet"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --log-level info
