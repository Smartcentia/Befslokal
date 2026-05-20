"""Feature flags – les og toggle system-innstillinger.

Offentlig lesing (auth påkrevd): GET /api/v1/feature-flags
Admin-toggle:                     POST /api/v1/feature-flags/{key}
"""
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.api.deps import get_db, get_current_user
from app.domains.core.models.user import User, UserRole
from app.models.system_settings import SystemSettings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Feature Flags"])

# Tillatne nøkler og standardverdier
_DEFAULTS: Dict[str, str] = {
    "hide_financials": "false",
}

# E-postadresser som alltid har tilgang til økonomidata uansett flagg
_FINANCIAL_BYPASS_EMAILS = {"frankvevle@gmail.com", "system@befs.no"}


async def _get_setting(db: AsyncSession, key: str) -> str:
    """Hent én innstilling; fallback til standard hvis den ikke finnes."""
    try:
        result = await db.execute(
            select(SystemSettings).where(SystemSettings.key == key)
        )
        row = result.scalar_one_or_none()
        return row.value if row else _DEFAULTS.get(key, "false")
    except Exception:
        return _DEFAULTS.get(key, "false")


@router.get("/feature-flags")
async def get_feature_flags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Returnerer gjeldende feature-flagg for innlogget bruker.

    `show_financials` = True  → bruker skal se økonomidata
    `show_financials` = False → økonomidata er skjult
    """
    hide_raw = await _get_setting(db, "hide_financials")
    hide = hide_raw.lower() == "true"

    is_admin = current_user.role == UserRole.ADMIN
    bypass = current_user.email in _FINANCIAL_BYPASS_EMAILS

    # Admin og eiere ser alltid økonomidata
    show_financials = not hide or is_admin or bypass

    return {
        "hide_financials": hide,
        "show_financials": show_financials,
        "is_admin": is_admin,
    }


@router.post("/feature-flags/{key}")
async def toggle_feature_flag(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Toggle (snu) en feature-flagg.
    Kun ADMIN eller eier-e-post kan bruke dette endepunktet.
    """
    is_admin = current_user.role == UserRole.ADMIN
    bypass = current_user.email in _FINANCIAL_BYPASS_EMAILS

    if not is_admin and not bypass:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kun administratorer kan endre feature-flagg",
        )

    if key not in _DEFAULTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ukjent flagg: {key}",
        )

    current_val = await _get_setting(db, key)
    new_val = "false" if current_val.lower() == "true" else "true"

    try:
        await db.execute(
            text(
                "INSERT INTO system_settings (key, value, updated_by, updated_at) "
                "VALUES (:key, :value, :by, :at) "
                "ON CONFLICT (key) DO UPDATE SET value = :value, updated_by = :by, updated_at = :at"
            ),
            {
                "key": key,
                "value": new_val,
                "by": current_user.email,
                "at": datetime.now(timezone.utc),
            },
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error("Kunne ikke lagre feature-flagg %s: %s", key, e)
        raise HTTPException(status_code=500, detail="Lagring feilet")

    logger.info("Feature-flagg '%s' endret til '%s' av %s", key, new_val, current_user.email)
    return {"key": key, "value": new_val, "updated_by": current_user.email}
