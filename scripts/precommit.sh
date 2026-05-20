#!/usr/bin/env bash
set -euo pipefail

# Pre-commit hook: ensure docs/python.md is up-to-date
ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$ROOT_DIR"

echo "[pre-commit] Generating Python docs..."
python3 scripts/generate_python_docs.py

if ! git diff --quiet -- docs/python.md; then
  echo "[pre-commit] docs/python.md updated by generator. Staging changes..."
  git add docs/python.md
fi

echo "[pre-commit] OK"

# To install:
#   chmod +x scripts/precommit.sh
#   ln -sf "$(pwd)/scripts/precommit.sh" .git/hooks/pre-commit
