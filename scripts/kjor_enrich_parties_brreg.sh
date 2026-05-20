#!/usr/bin/env bash
# Kjør BRREG-berikelse for alle partier med orgnr (e-post, telefon, adresse fra Enhetsregisteret).
# Bruk: fra prosjektrot: ./scripts/kjor_enrich_parties_brreg.sh
#       kun rapport:   ./scripts/kjor_enrich_parties_brreg.sh --dry-run

set -e
cd "$(dirname "$0")/../backend"
exec python3 -m app.scripts.enrich_parties_brreg_by_orgnr "$@"
