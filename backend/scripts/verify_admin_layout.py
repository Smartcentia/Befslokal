#!/usr/bin/env python3
"""
Rask regresjon uten å importere FastAPI (unngår tunge importkjeder).

Kjør fra backend-mappen:
  python3 scripts/verify_admin_layout.py
"""
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    init_path = BACKEND_ROOT / "app/api/v1/admin/__init__.py"
    text = init_path.read_text(encoding="utf-8")
    assert "evolution_router" in text and "include_router(evolution_router" in text, (
        "admin/__init__.py må inkludere evolution_router"
    )

    legacy = BACKEND_ROOT / "app/api/v1/admin.py"
    assert not legacy.exists(), f"Fjernet forventet: {legacy} (bruk app.api.v1.admin-pakken)"

    glossary = BACKEND_ROOT / "app/api/v1/endpoints/glossary.py"
    gtxt = glossary.read_text(encoding="utf-8")
    assert "get_current_active_superuser" in gtxt and "/scan" in gtxt, (
        "POST /glossary/scan skal kreve admin"
    )

    agent = BACKEND_ROOT / "app/domains/innsikt/routers/agent.py"
    atxt = agent.read_text(encoding="utf-8")
    assert "batch_risk_update" in atxt and "get_current_active_superuser" in atxt, (
        "batch-risk-update skal kreve admin"
    )

    client_ts = BACKEND_ROOT.parent / "frontend/lib/api/client.ts"
    ctxt = client_ts.read_text(encoding="utf-8")
    assert "endpoint.startsWith('/agent/admin')" in ctxt, (
        "client.ts skal behandle /agent/admin som admin-endepunkt ved impersonering"
    )

    print("verify_admin_layout: OK")


if __name__ == "__main__":
    main()
