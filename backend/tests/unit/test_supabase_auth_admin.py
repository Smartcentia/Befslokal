"""Tester for Supabase Auth Admin-hjelpere (mock av httpx)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import supabase_auth_admin as saa


@pytest.fixture
def configured_settings(monkeypatch):
    monkeypatch.setattr(saa.settings, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(saa.settings, "SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")


@pytest.mark.asyncio
async def test_supabase_auth_admin_configured_false_when_missing_url(monkeypatch):
    monkeypatch.setattr(saa.settings, "SUPABASE_URL", None)
    monkeypatch.setattr(saa.settings, "SUPABASE_SERVICE_ROLE_KEY", "key")
    assert saa.supabase_auth_admin_configured() is False


def _async_client_cm(inner: AsyncMock):
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=inner)
    cm.__aexit__ = AsyncMock(return_value=None)
    return cm


@pytest.mark.asyncio
async def test_create_supabase_user_success(configured_settings):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "auth-uuid-1", "email": "a@b.no"}

    inner = AsyncMock()
    inner.post = AsyncMock(return_value=mock_response)

    with patch("app.services.supabase_auth_admin.httpx.AsyncClient", return_value=_async_client_cm(inner)):
        data = await saa.create_supabase_user("a@b.no", "secretpass12")
        assert data["id"] == "auth-uuid-1"
        inner.post.assert_called_once()
        assert "/auth/v1/admin/users" in inner.post.call_args[0][0]


@pytest.mark.asyncio
async def test_create_supabase_user_raises_on_422(configured_settings):
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.json.return_value = {"msg": "User already registered"}

    inner = AsyncMock()
    inner.post = AsyncMock(return_value=mock_response)

    with patch("app.services.supabase_auth_admin.httpx.AsyncClient", return_value=_async_client_cm(inner)):
        with pytest.raises(saa.SupabaseAuthAdminError) as e:
            await saa.create_supabase_user("a@b.no", "secretpass12")
        assert e.value.status_code == 422


def test_humanize_create_error_duplicate():
    msg = saa.humanize_create_error("User already registered")
    assert "allerede" in msg.lower() or "registrert" in msg.lower()


@pytest.mark.asyncio
async def test_delete_supabase_user_success(configured_settings):
    mock_response = MagicMock()
    mock_response.status_code = 204

    inner = AsyncMock()
    inner.delete = AsyncMock(return_value=mock_response)

    with patch("app.services.supabase_auth_admin.httpx.AsyncClient", return_value=_async_client_cm(inner)):
        ok = await saa.delete_supabase_user("auth-uuid-1")
        assert ok is True
