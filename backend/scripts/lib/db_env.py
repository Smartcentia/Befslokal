"""
Validering av DATABASE_URL før script kobler til Postgres (unngår lange asyncpg-traces).
"""
from __future__ import annotations

import socket
import sys
from urllib.parse import urlparse


def require_database_url_for_local_scripts() -> None:
    """
    Avslutt med tydelig melding hvis URL mangler, er ugyldig, er Railway-intern,
    eller vertsnavnet ikke kan slås opp lokalt (gaierror).
    """
    from app.core.config import settings

    url = str(settings.DATABASE_URL or "").strip()
    if not url:
        print(
            "FEIL: DATABASE_URL er ikke satt. Opprett backend/.env (se .env.example) med "
            "postgresql+asyncpg://... — f.eks. Supabase Session Pooler. Lokalt: ikke *.railway.internal.",
            file=sys.stderr,
        )
        sys.exit(1)

    host = ""
    if "@" in url:
        host = url.split("@")[1].split(":")[0].split("/")[0]
    if not host or host == "host":
        print("FEIL: DATABASE_URL har ugyldig vert (host). Sjekk strengen.", file=sys.stderr)
        sys.exit(1)
    if host.endswith(".railway.internal"):
        print(
            "FEIL: *.railway.internal lar seg ikke koble til fra lokal maskin. "
            "Bruk Supabase pooler-URL i backend/.env, eller: railway run -- ...",
            file=sys.stderr,
        )
        sys.exit(1)

    raw = url
    if raw.startswith("postgresql+asyncpg://"):
        raw = "postgresql://" + raw[len("postgresql+asyncpg://") :]
    try:
        parsed = urlparse(raw)
    except Exception:
        print("FEIL: DATABASE_URL kunne ikke parses.", file=sys.stderr)
        sys.exit(1)

    dns_host = parsed.hostname or ""
    port = parsed.port or 5432
    if not dns_host:
        print("FEIL: DATABASE_URL mangler hostname.", file=sys.stderr)
        sys.exit(1)

    try:
        socket.getaddrinfo(dns_host, port, type=socket.SOCK_STREAM)
    except OSError as e:
        print(
            f"FEIL: Kan ikke slå opp databasens vertsnavn i DNS ({dns_host}:{port}): {e}. "
            "Sjekk nettverk/VPN og at URL er riktig (f.eks. Supabase pooler, ikke intern Railway-host).",
            file=sys.stderr,
        )
        sys.exit(1)
