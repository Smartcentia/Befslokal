import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

# Ensure app settings import does not fail in tests
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://dummy:dummy@localhost/dummy")
sys.path.append(os.getcwd())

from app.api.v1.admin.system import PropertyEnrichmentRequest, run_property_enrichment_batch


@pytest.mark.asyncio
async def test_run_property_enrichment_batch_returns_summary():
    fake_report = {
        "baseline_before": {"total_properties": 10},
        "baseline_after": {"total_properties": 10},
        "updated": {"properties_touched": 3, "names": 2, "images": 1},
        "skipped_no_match": 4,
        "skipped_low_score": 2,
        "samples": [{"property_id": "abc"}],
    }

    with patch("app.api.v1.admin.system.run_enrichment", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = fake_report

        req = PropertyEnrichmentRequest(
            apply=False,
            min_score=0.7,
            force_description=False,
            download_images=False,
            limit=25,
        )

        result = await run_property_enrichment_batch(req)

        assert result["message"] == "Property enrichment completed"
        assert result["mode"] == "dry-run"
        assert "summary" in result
        assert result["summary"]["updated"]["properties_touched"] == 3
        assert result["samples"][0]["property_id"] == "abc"
        mock_run.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_property_enrichment_batch_requires_confirm_apply():
    req = PropertyEnrichmentRequest(
        apply=True,
        confirm_apply=False,
        min_score=0.7,
    )

    with pytest.raises(HTTPException) as exc:
        await run_property_enrichment_batch(req)

    assert exc.value.status_code == 400
    assert "confirm_apply" in str(exc.value.detail)
