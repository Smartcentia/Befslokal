"""Unit tests for core domain models."""
import pytest
from uuid import uuid4
from datetime import datetime


@pytest.mark.unit
class TestPropertyModel:
    """Tests for Property model."""
    
    def test_property_creation(self):
        """Test creating a property instance."""
        from app.domains.core.models.property import Property
        
        property = Property(
            property_id=str(uuid4()),
            address="Testveien 1",
            postal_code="0001",
            city="Oslo",
            latitude=59.9139,
            longitude=10.7522,
        )
        
        assert property.address == "Testveien 1"
        assert property.city == "Oslo"
        assert property.latitude == 59.9139
    
    def test_property_validation(self):
        """Test property validation."""
        from app.domains.core.models.property import Property
        
        # Test with invalid latitude
        with pytest.raises(Exception):
            Property(
                property_id=str(uuid4()),
                address="Test",
                postal_code="0001",
                city="Oslo",
                latitude=91.0,  # Invalid
                longitude=10.7522,
            )


@pytest.mark.unit
class TestUnitModel:
    """Tests for Unit model."""
    
    def test_unit_creation(self):
        """Test creating a unit instance."""
        from app.domains.core.models.unit import Unit
        
        property_id = str(uuid4())
        unit = Unit(
            unit_id=str(uuid4()),
            property_id=property_id,
            purpose="Leilighet",
            area_sqm=50.0,
            floor=1,
        )
        
        assert unit.property_id == property_id
        assert unit.purpose == "Leilighet"
        assert unit.area_sqm == 50.0


@pytest.mark.unit
class TestPartyModel:
    """Tests for Party model."""
    
    def test_party_creation(self):
        """Test creating a party instance."""
        from app.domains.core.models.party import Party
        
        party = Party(
            party_id=str(uuid4()),
            name="Test AS",
            orgnr="123456789",
            contact_email="test@example.com",
            contact_phone="+4712345678",
        )
        
        assert party.name == "Test AS"
        assert party.orgnr == "123456789"


@pytest.mark.unit
class TestContractModel:
    """Tests for Contract model."""
    
    def test_contract_creation(self):
        """Test creating a contract instance."""
        from app.domains.core.models.contract import Contract
        
        contract = Contract(
            contract_id=str(uuid4()),
            unit_id=str(uuid4()),
            party_id=str(uuid4()),
            status="active",
            periods=[
                {
                    "start_date": "2024-01-01T00:00:00Z",
                    "end_date": "2024-12-31T23:59:59Z",
                    "index_name": "KPI",
                }
            ],
            amount={
                "currency": "NOK",
                "amount_per_year": 120000.0,
            },
            signed_at="2023-12-01T00:00:00Z",
        )
        
        assert contract.status == "active"
        assert len(contract.periods) == 1
        assert contract.amount["currency"] == "NOK"
