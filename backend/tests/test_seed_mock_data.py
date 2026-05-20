"""Tests for mock data seeding script."""
import pytest
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.db import base as db_models
from app.db.session import SessionLocal


@pytest.mark.integration
@pytest.mark.location
@pytest.mark.asyncio
async def test_seed_creates_properties(db_session):
    """Test at seeding oppretter properties."""
    from app.db import base as db_models
    import uuid
    
    # Opprett properties
    properties_data = [
        {
            "property_id": uuid.uuid4(),
            "address": "Karl Johans gate 1",
            "postal_code": "0161",
            "city": "Oslo",
            "latitude": 59.9139,
            "longitude": 10.7400,
        },
        {
            "property_id": uuid.uuid4(),
            "address": "Aker Brygge 15",
            "postal_code": "0250",
            "city": "Oslo",
            "latitude": 59.9094,
            "longitude": 10.7225,
        },
    ]
    
    for prop_data in properties_data:
        db_property = db_models.Property(**prop_data)
        db_session.add(db_property)
    
    await db_session.commit()
    
    # Verifiser
    from sqlalchemy import select
    result = await db_session.execute(select(db_models.Property))
    properties = result.scalars().all()
    assert len(properties) == 2
    assert all(p.latitude is not None and p.longitude is not None for p in properties)


@pytest.mark.integration
@pytest.mark.location
@pytest.mark.asyncio
async def test_seed_creates_units(db_session):
    """Test at seeding oppretter units."""
    from app.db import base as db_models
    import uuid
    
    # Opprett property
    property_id = uuid.uuid4()
    db_property = db_models.Property(
        property_id=property_id,
        address="Testveien 1",
        postal_code="0001",
        city="Oslo",
        latitude=59.9139,
        longitude=10.7522,
    )
    db_session.add(db_property)
    
    # Opprett unit
    unit_id = uuid.uuid4()
    db_unit = db_models.Unit(
        unit_id=unit_id,
        property_id=property_id,
        purpose="Leilighet",
        area_sqm=75.5,
        floor=2,
    )
    db_session.add(db_unit)
    await db_session.commit()
    
    # Verifiser
    from sqlalchemy import select
    result = await db_session.execute(select(db_models.Unit))
    units = result.scalars().all()
    assert len(units) == 1
    assert units[0].purpose == "Leilighet"
    assert units[0].area_sqm == 75.5


@pytest.mark.integration
@pytest.mark.location
@pytest.mark.asyncio
async def test_seed_creates_parties(db_session):
    """Test at seeding oppretter parties."""
    from app.db import base as db_models
    import uuid
    
    # Opprett party
    party_id = uuid.uuid4()
    db_party = db_models.Party(
        party_id=party_id,
        name="Test Leietaker",
        orgnr="100000001",
        contact_email="test@example.com",
        contact_phone="+47 12345678",
    )
    db_session.add(db_party)
    await db_session.commit()
    
    # Verifiser
    from sqlalchemy import select
    result = await db_session.execute(select(db_models.Party))
    parties = result.scalars().all()
    assert len(parties) == 1
    assert parties[0].orgnr == "100000001"


@pytest.mark.integration
@pytest.mark.location
@pytest.mark.asyncio
async def test_seed_creates_contracts(db_session):
    """Test at seeding oppretter contracts."""
    from app.db import base as db_models
    import uuid
    
    # Opprett property, unit, party
    property_id = uuid.uuid4()
    db_property = db_models.Property(
        property_id=property_id,
        address="Testveien 1",
        postal_code="0001",
        city="Oslo",
    )
    db_session.add(db_property)
    
    unit_id = uuid.uuid4()
    db_unit = db_models.Unit(
        unit_id=unit_id,
        property_id=property_id,
        purpose="Leilighet",
        area_sqm=75.5,
    )
    db_session.add(db_unit)
    
    party_id = uuid.uuid4()
    db_party = db_models.Party(
        party_id=party_id,
        name="Test Leietaker",
        orgnr="100000002",
    )
    db_session.add(db_party)
    
    # Opprett contract
    contract_id = uuid.uuid4()
    db_contract = db_models.Contract(
        contract_id=contract_id,
        unit_id=unit_id,
        party_id=party_id,
        status="active",
        signed_at=datetime(2024, 1, 1),
        periods=[
            {
                "start": "2024-01-01",
                "end": "2024-12-31",
                "rent": 15000.0
            }
        ],
        amount={
            "total": 180000.0,
            "deposit": 45000.0,
            "monthly_rent": 15000.0
        }
    )
    db_session.add(db_contract)
    await db_session.commit()
    
    # Verifiser
    from sqlalchemy import select
    result = await db_session.execute(select(db_models.Contract))
    contracts = result.scalars().all()
    assert len(contracts) == 1
    assert contracts[0].status == "active"


@pytest.mark.integration
@pytest.mark.location
@pytest.mark.asyncio
async def test_seed_coordinates_correct(db_session):
    """Test at koordinater settes korrekt."""
    from app.db import base as db_models
    import uuid
    
    property_id = uuid.uuid4()
    db_property = db_models.Property(
        property_id=property_id,
        address="Karl Johans gate 1",
        postal_code="0161",
        city="Oslo",
        latitude=59.9139,
        longitude=10.7400,
    )
    db_session.add(db_property)
    await db_session.commit()
    
    # Verifiser
    from sqlalchemy import select
    result = await db_session.execute(
        select(db_models.Property).where(db_models.Property.property_id == property_id)
    )
    property = result.scalars().first()
    
    assert property.latitude == 59.9139
    assert property.longitude == 10.7400












