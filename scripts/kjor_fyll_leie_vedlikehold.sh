#!/usr/bin/env bash
# Kjør: Finn eiendommer med 0 Leie (YTD) eller 0 Vedlikehold og fyll med syntetisk data.
# Bruk: fra prosjektrot: ./scripts/kjor_fyll_leie_vedlikehold.sh
#       kun rapport:   ./scripts/kjor_fyll_leie_vedlikehold.sh --dry-run

set -e
cd "$(dirname "$0")/../backend"
exec python3 scripts/finn_og_fyll_leie_vedlikehold.py "$@"
