#!/usr/bin/env bash
# Søk på nettet etter bilder for barnevernsinstitusjoner uten bilde.
# Bruk: fra prosjektrot: ./scripts/kjor_fetch_barnevern_images.sh
#       dry-run:        ./scripts/kjor_fetch_barnevern_images.sh --dry-run
#       begrenset:      ./scripts/kjor_fetch_barnevern_images.sh --limit 5
#       uten LLM:       ./scripts/kjor_fetch_barnevern_images.sh --no-llm

set -e
cd "$(dirname "$0")/../backend"
exec python3 scripts/fetch_images_for_barnevern.py "$@"
