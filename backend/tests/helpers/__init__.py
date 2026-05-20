"""Test helpers and utilities for backend testing."""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_property_data(
        address: str = "Testveien 1",
        postal_code: str = "0001",
        city: str = "Oslo",
        **kwargs
    ) -> Dict[str, Any]:
        """Create property test data."""
        data = {
            "property_id": str(uuid.uuid4()),
            "address": address,
            "postal_code": postal_code,
            "city": city,
            "latitude": 59.9139,
            "longitude": 10.7522,
        }
        data.update(kwargs)
        return data
    
    @staticmethod
    def create_unit_data(
        property_id: str,
        purpose: str = "Leilighet",
        area_sqm: float = 50.0,
        **kwargs
    ) -> Dict[str, Any]:
        """Create unit test data."""
        data = {
            "unit_id": str(uuid.uuid4()),
            "property_id": property_id,
            "purpose": purpose,
            "area_sqm": area_sqm,
            "floor": 1,
        }
        data.update(kwargs)
        return data
    
    @staticmethod
    def create_party_data(
        name: str = "Test AS",
        orgnr: str = "123456789",
        **kwargs
    ) -> Dict[str, Any]:
        """Create party test data."""
        data = {
            "party_id": str(uuid.uuid4()),
            "name": name,
            "orgnr": orgnr,
            "contact_email": f"{name.lower().replace(' ', '')}@example.com",
            "contact_phone": "+4712345678",
        }
        data.update(kwargs)
        return data
    
    @staticmethod
    def create_contract_data(
        unit_id: str,
        party_id: str,
        status: str = "active",
        **kwargs
    ) -> Dict[str, Any]:
        """Create contract test data."""
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=365)
        
        data = {
            "contract_id": str(uuid.uuid4()),
            "unit_id": unit_id,
            "party_id": party_id,
            "status": status,
            "periods": [
                {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "index_name": "KPI",
                }
            ],
            "amount": {
                "currency": "NOK",
                "amount_per_year": 120000.0,
            },
            "signed_at": (start_date - timedelta(days=30)).isoformat(),
        }
        data.update(kwargs)
        return data
    
    @staticmethod
    def create_user_data(
        email: str = "testuser@befs.no",
        name: str = "Test User",
        role: str = "user",
        **kwargs
    ) -> Dict[str, Any]:
        """Create user test data."""
        data = {
            "email": email,
            "name": name,
            "role": role,
            "image": None,
        }
        data.update(kwargs)
        return data


class DatabaseHelpers:
    """Helpers for database operations in tests."""
    
    @staticmethod
    async def create_property(db: AsyncSession, data: Optional[Dict[str, Any]] = None):
        """Create a property in the test database."""
        from app.domains.core.models.property import Property
        
        if data is None:
            data = TestDataFactory.create_property_data()
        
        property_obj = Property(**data)
        db.add(property_obj)
        await db.commit()
        await db.refresh(property_obj)
        return property_obj
    
    @staticmethod
    async def create_unit(db: AsyncSession, property_id: str, data: Optional[Dict[str, Any]] = None):
        """Create a unit in the test database."""
        from app.domains.core.models.unit import Unit
        
        if data is None:
            data = TestDataFactory.create_unit_data(property_id)
        
        unit_obj = Unit(**data)
        db.add(unit_obj)
        await db.commit()
        await db.refresh(unit_obj)
        return unit_obj
    
    @staticmethod
    async def create_party(db: AsyncSession, data: Optional[Dict[str, Any]] = None):
        """Create a party in the test database."""
        from app.domains.core.models.party import Party
        
        if data is None:
            data = TestDataFactory.create_party_data()
        
        party_obj = Party(**data)
        db.add(party_obj)
        await db.commit()
        await db.refresh(party_obj)
        return party_obj
    
    @staticmethod
    async def create_contract(
        db: AsyncSession,
        unit_id: str,
        party_id: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Create a contract in the test database."""
        from app.domains.core.models.contract import Contract
        from datetime import datetime
        
        if data is None:
            data = TestDataFactory.create_contract_data(unit_id, party_id)
        
        # Parse signed_at if string (SQLite fix)
        if "signed_at" in data and isinstance(data["signed_at"], str):
            try:
                data["signed_at"] = datetime.fromisoformat(data["signed_at"])
            except ValueError:
                pass # Already object or invalid
        
        contract_obj = Contract(**data)
        db.add(contract_obj)
        await db.commit()
        await db.refresh(contract_obj)
        return contract_obj
    
    @staticmethod
    async def cleanup_all(db: AsyncSession):
        """Clean up all test data."""
        from app.domains.core.models.contract import Contract
        from app.domains.core.models.unit import Unit
        from app.domains.core.models.party import Party
        from app.domains.core.models.property import Property
        
        # Delete in correct order to avoid FK constraints
        await db.execute("DELETE FROM contracts")
        await db.execute("DELETE FROM units")
        await db.execute("DELETE FROM parties")
        await db.execute("DELETE FROM properties")
        await db.commit()


class APITestHelpers:
    """Helpers for API testing."""
    
    @staticmethod
    def assert_response_ok(response, expected_status: int = 200):
        """Assert that response is OK."""
        assert response.status_code == expected_status, \
            f"Expected {expected_status}, got {response.status_code}: {response.text}"
    
    @staticmethod
    def assert_validation_error(response, field: Optional[str] = None):
        """Assert that response is a validation error."""
        assert response.status_code == 422, \
            f"Expected 422, got {response.status_code}: {response.text}"
        
        if field:
            data = response.json()
            detail = data.get("detail", [])
            fields = [err.get("loc", [])[-1] for err in detail if "loc" in err]
            assert field in fields, \
                f"Field '{field}' not in validation errors: {fields}"
    
    @staticmethod
    def assert_not_found(response):
        """Assert that response is 404 Not Found."""
        assert response.status_code == 404, \
            f"Expected 404, got {response.status_code}: {response.text}"
    
    @staticmethod
    def assert_unauthorized(response):
        """Assert that response is 401 Unauthorized."""
        assert response.status_code == 401, \
            f"Expected 401, got {response.status_code}: {response.text}"
    
    @staticmethod
    def assert_forbidden(response):
        """Assert that response is 403 Forbidden."""
        assert response.status_code == 403, \
            f"Expected 403, got {response.status_code}: {response.text}"


class MockExternalAPIs:
    """Mock external API responses for testing."""
    
    @staticmethod
    def brreg_response(orgnr: str = "123456789", name: str = "Test Firma AS"):
        """Mock BRREG response."""
        return {
            "organisasjonsnummer": orgnr,
            "navn": name,
            "organisasjonsform": {"beskrivelse": "Aksjeselskap"},
            "forretningsadresse": {
                "adresse": ["Gate 1"],
                "postnummer": "0001",
                "poststed": "Oslo"
            }
        }
    
    @staticmethod
    def kartverket_response(lat: float = 59.9139, lon: float = 10.7522):
        """Mock Kartverket geocoding response."""
        return {
            "adresser": [
                {
                    "representasjonspunkt": {
                        "lat": lat,
                        "lon": lon
                    },
                    "adressetekst": "Karl Johans gate 1",
                    "postnummer": "0161",
                    "poststed": "Oslo"
                }
            ]
        }
    
    @staticmethod
    def nve_response():
        """Mock NVE API response."""
        return {
            "flomsoner": [],
            "vannkraft": [],
            "energiinfrastruktur": []
        }
    
    @staticmethod
    def frost_response():
        """Mock Frost (MET) weather response."""
        return {
            "data": [
                {
                    "observations": [
                        {
                            "elementId": "air_temperature",
                            "value": 15.5,
                            "unit": "degC"
                        }
                    ]
                }
            ]
        }
