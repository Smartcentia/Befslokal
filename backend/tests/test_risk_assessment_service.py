"""Unit tests for RiskAssessmentService."""
import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from app.services.risk_assessment_service import RiskAssessmentService
from app.db import base as models
# from app.db.session import SessionLocal # Not needed if using fixture
from sqlalchemy import select

# Use db_session from conftest (which comes from db_session fixture)

@pytest_asyncio.fixture
async def test_property(db_session):
    """Create test property."""
    property = models.Property(
        address="Test gate 1",
        postal_code="0001",
        city="Oslo",
        latitude=59.9139,
        longitude=10.7522
    )
    db_session.add(property)
    await db_session.commit()
    await db_session.refresh(property)
    return property


@pytest_asyncio.fixture
async def test_proximity_services(db_session, test_property):
    """Create test proximity services."""
    services = []
    
    # Hospital - close
    service = models.ProximityService(
        property_id=test_property.property_id,
        service_type="hospital",
        service_name="Test Hospital",
        distance_meters=500,
        travel_time_minutes=5,
        latitude=59.915,
        longitude=10.754,
        rating=4.5,
        address="Hospital St 1",
        data_source="test",
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    services.append(service)
    db_session.add(service)
    
    # Pharmacy - medium distance
    service = models.ProximityService(
        property_id=test_property.property_id,
        service_type="pharmacy",
        service_name="Test Pharmacy",
        distance_meters=2500,
        travel_time_minutes=8,
        latitude=59.920,
        longitude=10.758,
        rating=4.0,
        address="Pharmacy St 1",
        data_source="test",
        expires_at=datetime.utcnow() + timedelta(days=30)
    )
    services.append(service)
    db_session.add(service)
    
    await db_session.commit()
    return services


@pytest.mark.asyncio
async def test_categorize_risk(db_session):
    """Test risk categorization."""
    # Internal methods, doesn't need DB usually, but service init requires it
    service = RiskAssessmentService(db_session)
    
    assert service._categorize_risk(10) == "low"
    assert service._categorize_risk(30) == "medium"
    assert service._categorize_risk(60) == "high"
    assert service._categorize_risk(80) == "critical"


@pytest.mark.asyncio
async def test_calculate_distance_risk(db_session):
    """Test distance risk calculation."""
    service = RiskAssessmentService(db_session)
    
    assert service._calculate_distance_risk(500) == 1
    assert service._calculate_distance_risk(1500) == 3
    assert service._calculate_distance_risk(3000) == 6
    assert service._calculate_distance_risk(8000) == 8
    assert service._calculate_distance_risk(15000) == 10


@pytest.mark.asyncio
async def test_calculate_time_risk(db_session):
    """Test time risk calculation."""
    service = RiskAssessmentService(db_session)
    
    assert service._calculate_time_risk(3) == 1
    assert service._calculate_time_risk(8) == 3
    assert service._calculate_time_risk(15) == 6
    assert service._calculate_time_risk(25) == 8
    assert service._calculate_time_risk(40) == 10


@pytest.mark.asyncio
async def test_calculate_accessibility_risk_no_data():
    """Test accessibility risk calculation with no proximity data."""
    db_mock = AsyncMock()
    service = RiskAssessmentService(db_mock)
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    db_mock.execute.return_value = mock_result
    
    result = await service.calculate_accessibility_risk(uuid4())
    
    assert result["risk_score"] == 100
    assert result["risk_category"] == "critical"
    assert "Ingen proximity data" in result["message"]


@pytest.mark.asyncio
async def test_calculate_accessibility_risk_with_data():
    """Test accessibility risk calculation with proximity data."""
    # Mock DB session
    db_mock = AsyncMock()
    service = RiskAssessmentService(db_mock)

    # Mock proximity service data
    prox_service = models.ProximityService(
        service_type="hospital",
        distance_meters=500,
        travel_time_minutes=5
    )
    prox_service2 = models.ProximityService(
        service_type="pharmacy",
        distance_meters=2500,
        travel_time_minutes=8
    )

    # Setup execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [prox_service, prox_service2]
    db_mock.execute.return_value = mock_result
    
    result = await service.calculate_accessibility_risk(uuid4())
    
    assert "risk_score" in result
    assert "risk_category" in result
    assert "factors" in result
    assert isinstance(result["factors"], list)
    assert len(result["factors"]) == 2
    assert result["risk_score"] >= 0
    assert result["risk_score"] <= 100


@pytest.mark.asyncio
async def test_create_risk_assessment():
    """Test creating risk assessment."""
    db_mock = AsyncMock()
    service = RiskAssessmentService(db_mock)
    
    # Mock accessibility risk result (internally calls execute)
    prox_service = models.ProximityService(
        service_type="hospital",
        distance_meters=500,
        travel_time_minutes=5
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [prox_service]
    db_mock.execute.return_value = mock_result

    assessment = await service.create_risk_assessment(
        property_id=uuid4(),
        methodology="MCDA"
    )
    
    assert assessment is not None
    assert assessment.methodology == "MCDA"
    
    # Verify commit called
    assert db_mock.commit.call_count >= 2


@pytest.mark.asyncio
async def test_get_latest_assessment():
    """Test getting latest assessment."""
    db_mock = AsyncMock()
    service = RiskAssessmentService(db_mock)
    
    mock_result = MagicMock()
    expected_assessment = models.RiskAssessment(assessment_id=uuid4())
    mock_result.scalars.return_value.first.return_value = expected_assessment
    db_mock.execute.return_value = mock_result
    
    # Get latest
    latest = await service.get_latest_assessment(uuid4())
    
    assert latest is not None
    assert latest.assessment_id == expected_assessment.assessment_id


@pytest.mark.asyncio
async def test_get_assessment_history():
    """Test getting assessment history."""
    db_mock = AsyncMock()
    service = RiskAssessmentService(db_mock)
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [models.RiskAssessment(), models.RiskAssessment()]
    db_mock.execute.return_value = mock_result
    
    # Get history
    history = await service.get_assessment_history(uuid4(), limit=10)
    
    assert len(history) == 2

