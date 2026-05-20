"""Tester for discontinued-properties endpoint."""

import pytest
from sqlalchemy import text

from app.domains.core.models.property import Property
from app.models.financial_models import Budget, GLTransaction


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_discontinued_properties_excludes_budgeted_property(client, db_session):
    """Eiendom med budsjett for år skal ikke havne i avviklet-listen."""
    p1 = Property(name="Aktiv i budsjett", address="A", city="Oslo", unit_id_erp="1001")
    p2 = Property(name="Uten budsjett", address="B", city="Oslo", unit_id_erp="1002")
    db_session.add_all([p1, p2])
    await db_session.flush()

    db_session.add(
        Budget(
            property_id=p1.property_id,
            year=2025,
            month=1,
            category="drift",
            amount=1000,
            is_synthetic=False,
            data_source="test",
        )
    )
    await db_session.commit()

    response = await client.get("/api/v1/properties/discontinued-properties?budget_year=2025&cost_year=2025")
    assert response.status_code == 200

    body = response.json()
    assert body["budget_available"] is True
    ids = {x["property_id"] for x in body["properties"]}
    assert str(p1.property_id) not in ids
    assert str(p2.property_id) in ids


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_discontinued_properties_excludes_properties_with_gl_costs(client, db_session):
    """Eiendommer med GL-kostnader i året skal ikke vises som avviklet."""
    p_with_prop_cost = Property(name="Med prop-kost", unit_id_erp="2001")
    p_with_dept_cost = Property(name="Med dept-kost", unit_id_erp="2002")
    p_without_cost = Property(name="Ingen kost", unit_id_erp="2003")
    db_session.add_all([p_with_prop_cost, p_with_dept_cost, p_without_cost])
    await db_session.flush()

    db_session.add_all(
        [
            GLTransaction(ar=2025, belop=5000, property_id=p_with_prop_cost.property_id),
            GLTransaction(ar=2025, belop=1200, dim1_kode="2002"),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/v1/properties/discontinued-properties?budget_year=2025&cost_year=2025")
    assert response.status_code == 200

    body = response.json()
    by_id = {row["property_id"]: row for row in body["properties"]}

    assert str(p_with_prop_cost.property_id) not in by_id
    assert str(p_with_dept_cost.property_id) not in by_id

    assert by_id[str(p_without_cost.property_id)]["has_costs_in_year"] is False
    assert by_id[str(p_without_cost.property_id)]["total_cost_in_year"] == pytest.approx(0)


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.asyncio
async def test_discontinued_properties_budget_table_missing_returns_fallback(client, db_session):
    """Hvis budget-tabellen mangler skal endpoint returnere fallback med budget_available=false."""
    p = Property(name="Fallback property", unit_id_erp="3001")
    db_session.add(p)
    await db_session.commit()

    await db_session.execute(text("DROP TABLE budget"))
    await db_session.commit()

    response = await client.get("/api/v1/properties/discontinued-properties?budget_year=2025&cost_year=2025")
    assert response.status_code == 200

    body = response.json()
    assert body["budget_available"] is False
    assert body["count"] == 1
    assert body["properties"][0]["property_id"] == str(p.property_id)
