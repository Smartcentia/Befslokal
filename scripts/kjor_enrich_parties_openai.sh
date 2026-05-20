#!/usr/bin/env bash
# Berik partier med orgnr: web-søk + OpenAI firmaoppsummering (lagres i external_data.openai_company_summary).
# Krever OPENAI_API_KEY. Bruk fra prosjektrot: ./scripts/kjor_enrich_parties_openai.sh
# Kun rapport: ./scripts/kjor_enrich_parties_openai.sh --dry-run
# Begrens antall: ./scripts/kjor_enrich_parties_openai.sh --limit 5

set -e
cd "$(dirname "$0")/../backend"
exec python3 -m app.scripts.enrich_parties_openai_company "$@"
