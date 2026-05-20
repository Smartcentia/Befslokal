"""
Supabase Auth Admin API (server-side only).
Bruker service role key – må aldri eksponeres til frontend.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

AUTH_ADMIN_USERS = "/auth/v1/admin/users"


class SupabaseAuthAdminError(Exception):
    """Feil fra Supabase Auth Admin API."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _headers() -> dict[str, str]:
    key = settings.SUPABASE_SERVICE_ROLE_KEY or ""
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _safe_error_text(response: httpx.Response) -> str:
    try:
        data = response.json()
        if isinstance(data, dict):
            return (
                data.get("msg")
                or data.get("message")
                or data.get("error_description")
                or str(data.get("error", data))
            )[:800]
    except Exception:
        pass
    return (response.text or "")[:800]


def supabase_auth_admin_configured() -> bool:
    return bool(
        settings.SUPABASE_URL
        and settings.SUPABASE_SERVICE_ROLE_KEY
        and settings.SUPABASE_URL.strip().startswith("https://")
    )


async def create_supabase_user(
    email: str,
    password: str,
    *,
    email_confirm: bool = True,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """
    Opprett bruker i Supabase Auth. Returnerer JSON-respons (inkl. 'id').
    """
    if not supabase_auth_admin_configured():
        raise SupabaseAuthAdminError(500, "Supabase Auth Admin is not configured")

    base = settings.SUPABASE_URL.strip().rstrip("/")
    url = f"{base}{AUTH_ADMIN_USERS}"
    payload = {
        "email": email.strip().lower(),
        "password": password,
        "email_confirm": email_confirm,
    }

    async def _post(c: httpx.AsyncClient) -> dict[str, Any]:
        response = await c.post(url, headers=_headers(), json=payload)
        if response.status_code not in (200, 201):
            detail = _safe_error_text(response)
            logger.warning(
                "Supabase admin create user failed: status=%s detail=%s",
                response.status_code,
                detail,
            )
            raise SupabaseAuthAdminError(response.status_code, detail)
        return response.json()

    if client is not None:
        return await _post(client)
    async with httpx.AsyncClient(timeout=30.0) as c:
        return await _post(c)


async def delete_supabase_user(
    user_id: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> bool:
    """Slett bruker i Supabase Auth (kompensasjon). Returnerer True ved suksess."""
    if not supabase_auth_admin_configured():
        logger.warning("delete_supabase_user: not configured, skip")
        return False

    base = settings.SUPABASE_URL.strip().rstrip("/")
    url = f"{base}{AUTH_ADMIN_USERS}/{user_id}"

    async def _delete(c: httpx.AsyncClient) -> bool:
        response = await c.delete(url, headers=_headers())
        if response.status_code in (200, 204):
            return True
        logger.warning(
            "Supabase admin delete user failed: status=%s body=%s",
            response.status_code,
            _safe_error_text(response),
        )
        return False

    if client is not None:
        return await _delete(client)
    async with httpx.AsyncClient(timeout=30.0) as c:
        return await _delete(c)


def humanize_create_error(detail: str) -> str:
    """Kort norsk/feiltekst til API-klient."""
    d = detail.lower()
    if "already" in d or "registered" in d or "exists" in d or "duplicate" in d:
        return "E-posten er allerede registrert i Supabase Auth"
    return detail or "Kunne ikke opprette bruker i Supabase Auth"
