"""Tester for GL Dim4-aggregering per eiendom."""
from decimal import Decimal
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_gl_costs_by_dim4_sums_by_dim4(client, db_session):
    from app.domains.core.models.property import Property as PropertyModel
    from app.models.financial_models import GLTransaction

    pid = uuid4()
    db_session.add(
        PropertyModel(
            property_id=pid,
            name="Test eiendom Dim4",
            address="Testveien 1",
            region="Nord",
        )
    )
    db_session.add(
        GLTransaction(
            transaction_id=uuid4(),
            belop=Decimal("500.00"),
            property_id=pid,
            ar=2025,
            dim4_kode="K100",
        )
    )
    db_session.add(
        GLTransaction(
            transaction_id=uuid4(),
            belop=Decimal("300.00"),
            property_id=pid,
            ar=2025,
            dim4_kode="K100",
        )
    )
    db_session.add(
        GLTransaction(
            transaction_id=uuid4(),
            belop=Decimal("100.00"),
            property_id=pid,
            ar=2025,
            dim4_kode=None,
        )
    )
    await db_session.commit()

    r = await client.get(
        f"/api/v1/properties/{pid}/gl-costs-by-dim4?year=2025",
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["property_id"] == str(pid)
    assert data["year"] == 2025
    assert data["total"] == 900.0
    assert len(data["rows"]) == 2
    by_kode = {row["dim4_kode"]: row["total"] for row in data["rows"]}
    assert by_kode["K100"] == 800.0
    unknown = sum(r["total"] for r in data["rows"] if r["dim4_kode"] is None)
    assert unknown == 100.0


@pytest.mark.asyncio
async def test_get_properties_region_filter(client, db_session):
    from app.domains.core.models.property import Property as PropertyModel

    p1 = uuid4()
    p2 = uuid4()
    db_session.add_all(
        [
            PropertyModel(
                property_id=p1,
                name="Nord-1",
                address="A1",
                region="Nord",
            ),
            PropertyModel(
                property_id=p2,
                name="Vest-1",
                address="A2",
                region="Vest",
            ),
        ]
    )
    await db_session.commit()

    r = await client.get(
        "/api/v1/properties?region=Nord&limit=100&source_coverage=all&include_risk=false",
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 200
    items = r.json()
    ids = {x["property_id"] for x in items}
    assert str(p1) in ids
    assert str(p2) not in ids
