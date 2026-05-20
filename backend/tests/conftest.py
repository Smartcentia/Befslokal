"""Pytest fixtures for testing."""

# DSPy bruker disk-cache ved import. Sett skrivbar cache-dir før noen test importerer dspy,
# slik at golden set (og andre dspy-tester) ikke feiler i readonly-miljø (f.eks. sandbox/CI).
import os
_tests_dir = os.path.dirname(os.path.abspath(__file__))
if "DSPY_CACHEDIR" not in os.environ:
    os.environ["DSPY_CACHEDIR"] = os.path.join(_tests_dir, ".pytest_dspy_cache")
# Speed up and stabilize app import for tests by skipping heavy admin router bootstrap.
if "BEFS_SKIP_ADMIN_ROUTER" not in os.environ:
    os.environ["BEFS_SKIP_ADMIN_ROUTER"] = "1"
# Last .env slik at DATABASE_URL er tilgjengelig når session importeres
_env_path = os.path.join(os.path.dirname(_tests_dir), ".env")
if os.path.exists(_env_path):
    from dotenv import load_dotenv
    load_dotenv(_env_path)

import pytest
import pytest_asyncio
import enum
from fastapi.testclient import TestClient
from httpx import AsyncClient
from httpx import ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base # This imports all models
from app.api.deps import get_db
from app.core.config import settings
from app.db import session


# Test database URL (in-memory SQLite for testing)
# Test database URL (in-memory SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Fix for SQLite UUID and Enum support
import sqlalchemy.types as types
from sqlalchemy import TypeDecorator, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

class GUID(TypeDecorator):
    """UUID type that works with SQLite."""
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(String(36))
        else:
            return dialect.type_descriptor(PG_UUID())
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'sqlite':
            return str(value) if not isinstance(value, str) else value
        else:
            return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'sqlite':
            return uuid.UUID(value) if isinstance(value, str) else value
        else:
            return value

# Patch models for SQLite compatibility
from app import models


# Replace UUID columns with GUID for SQLite
from sqlalchemy.dialects.postgresql import TSVECTOR, JSONB, ARRAY
from sqlalchemy.types import JSON

for table in Base.metadata.tables.values():
    for col in table.columns:
        if isinstance(col.type, PG_UUID):
            col.type = GUID()
        elif isinstance(col.type, TSVECTOR):
             col.type = String()
        elif isinstance(col.type, JSONB):
            col.type = JSON()
        elif isinstance(col.type, ARRAY):
            col.type = JSON() # SQLite doesn't have ARRAY, use JSON as proxy
        
        # Replace enum with String for SQLite
        try:
            if hasattr(col.type, 'python_type') and col.type.python_type is not None:
                if hasattr(col.type.python_type, '__bases__') and enum.Enum in col.type.python_type.__bases__:
                    col.type = String(20)
        except (NotImplementedError, AttributeError):
            # Skip types that don't support python_type
            pass

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Opprett test database session og tabeller."""
    # Ensure clean slate by dropping and creating tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create the session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        await session.close()
        # Cleanup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Test client med overstyrt database session og autentisering."""
    async def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    # Mock user for auth dependency
    from app.api.deps import get_current_user
    from app.domains.core.models.user import User, UserRole
    
    async def override_get_current_user():
        return User(
            email="test@befs.no",
            name="Test User",
            role=UserRole.ADMIN
        )
    
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Mock AuthMiddleware token verification
    from unittest.mock import AsyncMock
    from app.core.security import security_validator
    
    # Save original method to restore after test
    original_verify = security_validator.verify_token
    
    # Patch to return valid dict (simulating decoded token)
    security_validator.verify_token = AsyncMock(return_value={
        "sub": "test-user",
        "email": "test@befs.no",
        "roles": ["admin"],
    })
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Patch engine to prevent startup event from connecting to real DB
    session.engine = engine
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"Authorization": "Bearer test-token"}) as test_client:
        yield test_client
    
    # Restore
    app.dependency_overrides.clear()
    security_validator.verify_token = original_verify


@pytest.fixture
def sample_property():
    """Sample property data for testing."""
    return {
        "property_id": "123e4567-e89b-12d3-a456-426614174000",
        "address": "Testveien 1",
        "postal_code": "0001",
        "city": "Oslo",
        "latitude": 59.9139,
        "longitude": 10.7522,
    }


@pytest.fixture
def sample_unit(sample_property):
    """Sample unit data for testing."""
    return {
        "unit_id": "223e4567-e89b-12d3-a456-426614174000",
        "property_id": sample_property["property_id"],
        "purpose": "Leilighet",
        "area_sqm": 50.0,
        "floor": 1,
    }


@pytest.fixture
def sample_party():
    """Sample party data for testing."""
    return {
        "party_id": "323e4567-e89b-12d3-a456-426614174000",
        "name": "Test AS",
        "orgnr": "123456789",
        "contact_email": "test@example.com",
        "contact_phone": "+4712345678",
    }


@pytest.fixture
def sample_contract(sample_unit, sample_party):
    """Sample contract data for testing."""
    return {
        "contract_id": "423e4567-e89b-12d3-a456-426614174000",
        "unit_id": sample_unit["unit_id"],
        "party_id": sample_party["party_id"],
        "status": "active",
        "periods": [
            {
                "start_date": "2024-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z",
                "index_name": "KPI",
            }
        ],
        "amount": {
            "currency": "NOK",
            "amount_per_year": 120000.0,
        },
        "signed_at": "2023-12-01T00:00:00Z",
    }


@pytest.fixture
def sample_text_content():
    """Sample text content for testing."""
    return {
        "content": "Dette er en test tekst for import. Den inneholder viktig informasjon som skal indekseres i ChromaDB for semantisk søk.",
        "source_type": "file",
        "metadata": {"filename": "test.txt", "test": True}
    }


@pytest.fixture
def sample_json_data():
    """Sample JSON data for testing."""
    return {
        "name": "Test Kontrakt",
        "description": "Dette er en test kontrakt med viktig informasjon",
        "notes": "Viktig informasjon her som skal indekseres",
        "amount": 100000,
        "status": "active"
    }


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing."""
    return """address,postal_code,city,purpose,area_sqm,party_name,orgnr,status
Karl Johans gate 1,0161,Oslo,Kontor,50,Test Firma,123456789,active
Gate 2,5001,Bergen,Lager,100,Test AS,987654321,active"""


@pytest.fixture
def mock_bronnoysund_response():
    """Mock Brønnøysund API response."""
    return {
        "organisasjonsnummer": "123456789",
        "navn": "Test Firma AS",
        "organisasjonsform": {"beskrivelse": "Aksjeselskap"},
        "adresse": ["Gate 1", "0001 Oslo"],
        "postnummer": "0001",
        "poststed": "Oslo"
    }


@pytest.fixture
def mock_nve_response():
    """Mock NVE API response."""
    return {
        "flomsoner": [],
        "vannkraft": [],
        "energiinfrastruktur": []
    }


@pytest.fixture
def mock_kartverket_response():
    """Mock Kartverket API response."""
    return {
        "lat": 59.9139,
        "lon": 10.7522,
        "adresse": "Karl Johans gate 1",
        "postnummer": "0161",
        "kommune": "Oslo",
        "høyde": 10.5
    }


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatisk cleanup etter hver test."""
    yield
    # Cleanup vil kjøre etter test er ferdig
    # ChromaDB cleanup håndteres i test_vectordb.py med temp_chroma_path


@pytest.fixture
def mock_embeddings():
    """Mock embeddings generator for testing."""
    from unittest.mock import patch
    with patch("app.services.embeddings.generate_embeddings") as mock:
        # Standard mock embedding (384-dimensjonal vektor)
        mock.return_value = [[0.1] * 384]
        yield mock


# @pytest.fixture
# def sample_batch_job(db_session):
#     """Sample batch job for testing."""
#     # from app.services.batch_job_service import BatchJobService
#     
#     # job_service = BatchJobService(db_session)
#     # config = {
#     #     "sources": ["nve", "kartverket"],
#     #     # "force_refresh": False,
#     #     "radius": 1000,
#     #     "cache_expires_hours": 24,
#     #     "update_full_assessment": False,
#     # }
#     # job = job_service.create_job(
#     #     job_type="external_risk",
#     #     config=config,
#     # )
#     # return job
    pass


@pytest.fixture
def mock_external_apis():
    """Mock external APIs (NVE, Kartverket) for testing."""
    from unittest.mock import Mock
    from app.services.external_data_orchestrator import ExternalFetchResult
    from datetime import datetime, timedelta
    
    def _dummy_response(source: str):
        now = datetime.utcnow()
        return {
            "status": "success",
            "api_data_id": str(uuid.uuid4()),
            "data": {"source": source, "value": 1},
            "fetched_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=24)).isoformat(),
            "cache_origin": "live",
        }
    
    orchestrator = Mock()
    orchestrator.fetch_nve = Mock(return_value=ExternalFetchResult(
        response=_dummy_response("nve"),
        persisted=None,
        from_cache=False,
    ))
    orchestrator.fetch_kartverket = Mock(return_value=ExternalFetchResult(
        response=_dummy_response("kartverket"),
        persisted=None,
        from_cache=False,
    ))
    
    return orchestrator

