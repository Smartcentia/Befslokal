import json
from pathlib import Path

import pytest

import app.api.v1.admin.system as admin_system


@pytest.mark.asyncio
async def test_property_enrichment_report_list_and_get(client, tmp_path, monkeypatch):
    # Arrange: point report directory to temp and create deterministic files
    monkeypatch.setattr(admin_system, "_enrichment_reports_dir", lambda: Path(tmp_path))

    report_a = tmp_path / "property_enrichment_report_20260101T000000Z.json"
    report_b = tmp_path / "property_enrichment_report_20260102T000000Z.json"
    ignored = tmp_path / "other_report.json"

    report_a.write_text(json.dumps({"baseline_before": {"total_properties": 1}}), encoding="utf-8")
    report_b.write_text(json.dumps({"baseline_before": {"total_properties": 2}}), encoding="utf-8")
    ignored.write_text("{}", encoding="utf-8")

    # Act: list endpoint
    list_resp = await client.get("/api/v1/admin/property-enrichment/reports?limit=10")

    # Assert list
    assert list_resp.status_code == 200
    payload = list_resp.json()
    assert "reports" in payload
    assert len(payload["reports"]) == 2
    names = [r["filename"] for r in payload["reports"]]
    assert "property_enrichment_report_20260101T000000Z.json" in names
    assert "property_enrichment_report_20260102T000000Z.json" in names

    # Act: get endpoint for one file
    get_resp = await client.get("/api/v1/admin/property-enrichment/reports/property_enrichment_report_20260102T000000Z.json")

    # Assert get
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert detail["filename"] == "property_enrichment_report_20260102T000000Z.json"
    assert detail["report"]["baseline_before"]["total_properties"] == 2


@pytest.mark.asyncio
async def test_property_enrichment_report_get_rejects_invalid_filename(client):
    # Route params cannot contain slashes, so use a bad-but-routable filename
    # to exercise endpoint-level validation.
    resp = await client.get("/api/v1/admin/property-enrichment/reports/not_an_enrichment_report.json")
    assert resp.status_code == 400
