"""
Synkron klient for Stortingets åpne data (data.stortinget.no/eksport/...).
Brukes av skript; JSON med format=json.
Se https://data.stortinget.no/dokumentasjon-og-hjelp/
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

BASE = "https://data.stortinget.no/eksport"
USER_AGENT = "BEFS-Eiendomsbase/1.0 (Stortinget open data)"


class StortingetOpenDataClient:
    """Minimal GET-klient for forhåndsdefinerte eksport-URI-er."""

    def __init__(self, timeout: float = 60.0):
        self.timeout = timeout

    def _get_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{BASE}/{path.lstrip('/')}"
        q = dict(params or {})
        q["format"] = "json"
        with httpx.Client(timeout=self.timeout, headers={"User-Agent": USER_AGENT}) as client:
            r = client.get(url, params=q)
            r.raise_for_status()
            return r.json()

    def sesjoner(self) -> Dict[str, Any]:
        return self._get_json("sesjoner")

    def saker(self, sesjonid: str) -> Dict[str, Any]:
        return self._get_json("saker", {"sesjonid": sesjonid})

    def sak(self, sakid: int) -> Dict[str, Any]:
        return self._get_json("sak", {"sakid": sakid})

    def list_sesjon_ids(self, max_sessions: int = 12) -> List[str]:
        """Returnerer nyeste sesjons-ID-er først (ca. siste år)."""
        raw = self.sesjoner()
        lst = raw.get("sesjoner_liste") or []
        ids: List[str] = []
        for s in lst:
            sid = s.get("id")
            if sid and isinstance(sid, str):
                ids.append(sid)
        # API returnerer ofte fremtidige sesjoner først; sorter synkende på første årstall
        def sort_key(x: str) -> tuple:
            parts = x.split("-")
            try:
                return (int(parts[0]) if parts else 0, x)
            except ValueError:
                return (0, x)

        ids.sort(key=sort_key, reverse=True)
        return ids[:max_sessions]
