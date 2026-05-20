#!/bin/bash

# Script for å kjøre batch-oppdatering av nærliggende tjenester
set -e

# Sjekk om DATABASE_URL er satt, hvis ikke prøv å kilde .env eller config
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️ DATABASE_URL ikke satt. Prøver å finne den..."
    # Her kan du legge til logikk for å hente den fra en config-fil hvis ønskelig
    # For nå forventer vi at brukeren har den i miljøet eller setter den manuelt
    echo "Beskjed: Kjør scriptet slik: DATABASE_URL=... ./scripts/run_proximity_update.sh"
    exit 1
fi

echo "🚀 Starter batch-oppdatering av nærliggende tjenester..."

# Bruk den virtuelle venv-en hvis den finnes
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

python3 scripts/refresh_proximity_batch.py

echo "✅ Batch-kjøring fullført."
