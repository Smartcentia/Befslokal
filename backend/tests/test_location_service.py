"""Unit tests for location_service."""
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta

from app.services.location_service import get_location_info, fetch_and_cache_location_data
from app.domains.core.models.property import Property as PropertyModel
from app.models.external_api_data import ExternalApiData


import pytest_asyncio

@pytest_asyncio.fixture
async def sample_property_db(db_session):
    """Opprett property i database for testing."""
    property_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    db_property = PropertyModel(
        property_id=property_id,
        address="Testveien 1",
        postal_code="0001",
        city="Oslo",
        latitude=None,
        longitude=None,
    )
    db_session.add(db_property)
    await db_session.commit()
    await db_session.refresh(db_property)
    return db_property


@pytest_asyncio.fixture
async def sample_property_with_coords(db_session):
    """Opprett property med koordinater i database for testing."""
    property_id = UUID("223e4567-e89b-12d3-a456-426614174000")
    db_property = PropertyModel(
        property_id=property_id,
        address="Karl Johans gate 1",
        postal_code="0161",
        city="Oslo",
        latitude=59.9139,
        longitude=10.7522,
    )
    db_session.add(db_property)
    await db_session.commit()
    await db_session.refresh(db_property)
    return db_property


@pytest.mark.unit
@pytest.mark.location
@pytest.mark.asyncio
async def test_get_location_info_with_cached_data(db_session, sample_property_db):
    """Test henting av location-info med cachet data."""
    # Opprett property
    property_id = sample_property_db.property_id
    
    # Opprett cachet Kartverket-data
    first_data = ExternalApiData(
        source_api="kartverket",
        entity_type="property",
        entity_id=str(property_id),
        data={"høyde": 10.5, "kommune": "Oslo"},
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db_session.add(first_data)
    
    # Opprett cachet NVE-data
    nve_data = ExternalApiData(
        source_api="nve",
        entity_type="property",
        entity_id=str(property_id),
        data={"vannkraft": [], "flomsoner": []},
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db_session.add(nve_data)
    await db_session.commit()
    
    # Hent location-info
    result = await get_location_info(property_id, db_session)
    
    assert "property" in result
    assert "location_info" in result
    assert result["property"]["property_id"] == str(property_id)
    assert "kartverket" in result["location_info"]
    assert "nve" in result["location_info"]
    assert result["location_info"]["kartverket"]["høyde"] == 10.5


@pytest.mark.unit
@pytest.mark.location
@pytest.mark.asyncio
async def test_get_location_info_without_cache(db_session, sample_property_db):
    """Test henting av location-info uten cache."""
    property_id = sample_property_db.property_id
    
    result = await get_location_info(property_id, db_session)
    
    assert "property" in result
    assert "location_info" in result
    assert result["property"]["property_id"] == str(property_id)
    assert result["location_info"] == {}  # Ingen cachet data


@pytest.mark.unit
@pytest.mark.location
@pytest.mark.asyncio
async def test_get_location_info_expired_cache(db_session, sample_property_db):
    """Test henting av location-info med utløpt cache."""
    property_id = sample_property_db.property_id
    
    # Opprett utløpt cache
    kartverket_data = ExternalApiData(
        source_api="kartverket",
        entity_type="property",
        entity_id=str(property_id),
        data={"høyde": 10.5},
        expires_at=datetime.utcnow() - timedelta(hours=1)  # Utløpt
    )
    db_session.add(kartverket_data)
    await db_session.commit()
    
    result = await get_location_info(property_id, db_session)
    
    assert "kartverket" in result["location_info"]
    assert result["location_info"]["kartverket"]["expired"] is True


@pytest.mark.unit
@pytest.mark.location
@pytest.mark.asyncio
async def test_get_location_info_invalid_property_id(db_session):
    """Test henting av location-info med ugyldig property ID."""
    fake_id = uuid4()
    
    result = await get_location_info(fake_id, db_session)
    
    assert "error" in result
    assert "ikke funnet" in result["error"]


@pytest.mark.unit
@pytest.mark.location
@pytest.mark.slow
@pytest.mark.asyncio
async def test_fetch_and_cache_kartverket_data(db_session, sample_property_with_coords):
    """Test henting og caching av Kartverket-data."""
    property_id = sample_property_with_coords.property_id
    
    with patch("app.services.location_service.KartverketClient") as MockClient:
        mock_client = MagicMock()
        mock_client.fetch_property_data.return_value = {
            "høyde": 10.5,
            "kommune": "Oslo"
        }
        MockClient.return_value = mock_client
        
        with patch("app.services.location_service.index_api_data") as mock_index:
            mock_index.return_value = {"status": "success", "chunks_indexed": 1}
            
            result = await fetch_and_cache_location_data(
                property_id=property_id,
                db=db_session,
                fetch_kartverket=True,
                fetch_nve=False
            )
            
            assert "kartverket" in result
            assert result["kartverket"]["status"] == "success"
            assert "høyde" in result["kartverket"]["data"]
            
            # Verifiser at data er cachet (need to use async execute for query too or run_to_sync)
            from sqlalchemy import select
            q = select(ExternalApiData).filter(
                ExternalApiData.source_api == "kartverket",
                ExternalApiData.entity_id == str(property_id)
            )
            res = await db_session.execute(q)
            cached = res.scalar_one_or_none()
            
            assert cached is not None
            assert cached.data["høyde"] == 10.5


@pytest.mark.unit
@pytest.mark.location
@pytest.mark.slow
@pytest.mark.asyncio
async def test_fetch_and_cache_nve_data(db_session, sample_property_with_coords):
    """Test henting og caching av NVE-data."""
    property_id = sample_property_with_coords.property_id
    
    with patch("app.services.location_service.NVEClient") as MockClient:
        mock_client = MagicMock()
        mock_client.fetch_property_data.return_value = {
            "vannkraft": [],
            "flomsoner": []
        }
        MockClient.return_value = mock_client
        
        with patch("app.services.location_service.index_api_data") as mock_index:
            mock_index.return_value = {"status": "success", "chunks_indexed": 1}
            
            result = await fetch_and_cache_location_data(
                property_id=property_id,
                db=db_session,
                fetch_kartverket=False,
                fetch_nve=True
            )
            
            assert "nve" in result
            assert result["nve"]["status"] == "success"


@pytest.mark.unit
@pytest.mark.location
@pytest.mark.asyncio
async def test_fetch_and_cache_uses_existing_cache(db_session, sample_property_with_coords):
    """Test at eksisterende cache brukes hvis ikke utløpt."""
    property_id = sample_property_with_coords.property_id
    
    # Opprett eksisterende cache
    existing_data = ExternalApiData(
        source_api="kartverket",
        entity_type="property",
        entity_id=str(property_id),
        data={"høyde": 15.0},
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db_session.add(existing_data)
    await db_session.commit()
    
    with patch("app.services.location_service.KartverketClient") as MockClient:
        result = await fetch_and_cache_location_data(
            property_id=property_id,
            db=db_session,
            fetch_kartverket=True,
            fetch_nve=False
        )
        
        # Sjekk at status er "cached" og ikke "success"
        assert result["kartverket"]["status"] == "cached"
        # Client skal ikke være kalt
        assert not MockClient.called


@pytest.mark.unit
@pytest.mark.location
@pytest.mark.asyncio
async def test_fetch_and_cache_missing_coordinates(db_session, sample_property_db):
    """Test feilhåndtering når property mangler koordinater."""
    property_id = sample_property_db.property_id
    
    result = await fetch_and_cache_location_data(
        property_id=property_id,
        db=db_session,
        fetch_kartverket=True,
        fetch_nve=True
    )
    
    assert "error" in result
    assert "koordinater" in result["error"]


@pytest.mark.unit
@pytest.mark.location
@pytest.mark.asyncio
async def test_fetch_and_cache_invalid_property_id(db_session):
    """Test feilhåndtering med ugyldig property ID."""
    fake_id = uuid4()
    
    result = await fetch_and_cache_location_data(
        property_id=fake_id,
        db=db_session,
        fetch_kartverket=True,
        fetch_nve=True
    )
    
    assert "error" in result
    assert "ikke funnet" in result["error"]

