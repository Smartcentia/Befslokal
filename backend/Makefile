# Backend Makefile
.PHONY: test test-unit test-cov verify-admin

PY := $(shell cd "$(CURDIR)" && [ -x .venv/bin/python ] && echo .venv/bin/python || command -v python3)

# Kjør unit-tester (demp warnings) — bruk alltid venv slik at pytest/pygments stemmer
test: test-unit

test-unit:
	PYTHONWARNINGS=ignore $(PY) -m pytest tests/unit/ -q

# Rask sjekk av admin-wireup uten å importere FastAPI
verify-admin:
	$(PY) scripts/verify_admin_layout.py

test-cov:
	PYTHONWARNINGS=ignore $(PY) -m pytest tests/unit/ --cov=app --cov-report=term-missing -q
