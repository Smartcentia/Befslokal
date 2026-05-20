"""Integration tests for CRUD operations on core domain entities."""
import pytest
from httpx import AsyncClient
from tests.helpers import TestDataFactory, DatabaseHelpers, APITestHelpers



# Common headers for authenticated requests
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.mark.integration
@pytest.mark.requires_db
class TestPropertiesCRUD:
    """Tests for Properties CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_property(self, client: AsyncClient):
        """Test creating a new property."""
        property_data = TestDataFactory.create_property_data()
        
        response = await client.post("/api/v1/properties", json=property_data, headers=AUTH_HEADERS)
        APITestHelpers.assert_response_ok(response, 201)
        
        data = response.json()
        assert data["address"] == property_data["address"]
        assert data["city"] == property_data["city"]
    
    @pytest.mark.asyncio
    async def test_get_property(self, client: AsyncClient, db_session):
        """Test retrieving a property."""
        # Create property in DB
        property_obj = await DatabaseHelpers.create_property(db_session)
        
        response = await client.get(f"/api/v1/properties/{property_obj.property_id}", headers=AUTH_HEADERS)
        APITestHelpers.assert_response_ok(response)
        
        data = response.json()
        assert data["property_id"] == str(property_obj.property_id)
        assert data["address"] == property_obj.address
    
    @pytest.mark.asyncio
    async def test_list_properties(self, client: AsyncClient, db_session):
        """Test listing all properties."""
        # Create multiple properties
        await DatabaseHelpers.create_property(db_session, {"address": "Test 1"})
        await DatabaseHelpers.create_property(db_session, {"address": "Test 2"})
        
        response = await client.get("/api/v1/properties", headers=AUTH_HEADERS)
        APITestHelpers.assert_response_ok(response)
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    @pytest.mark.asyncio
    async def test_update_property(self, client: AsyncClient, db_session):
        """Test updating a property."""
        property_obj = await DatabaseHelpers.create_property(db_session)
        
        update_data = {"address": "Updated Address"}
        response = await client.patch(
            f"/api/v1/properties/{property_obj.property_id}",
            json=update_data,
            headers=AUTH_HEADERS
        )
        APITestHelpers.assert_response_ok(response)
        
        data = response.json()
        assert data["address"] == "Updated Address"
    
    @pytest.mark.asyncio
    async def test_delete_property(self, client: AsyncClient, db_session):
        """Test deleting a property."""
        property_obj = await DatabaseHelpers.create_property(db_session)
        
        response = await client.delete(f"/api/v1/properties/{property_obj.property_id}", headers=AUTH_HEADERS)
        assert response.status_code in [200, 204]
        
        # Verify deletion
        response = await client.get(f"/api/v1/properties/{property_obj.property_id}", headers=AUTH_HEADERS)
        APITestHelpers.assert_not_found(response)
    
    @pytest.mark.asyncio
    async def test_property_not_found(self, client: AsyncClient):
        """Test getting non-existent property."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/properties/{fake_id}", headers=AUTH_HEADERS)
        APITestHelpers.assert_not_found(response)


@pytest.mark.integration
@pytest.mark.requires_db
class TestContractsCRUD:
    """Tests for Contracts CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_contract(self, client: AsyncClient, db_session):
        """Test creating a new contract."""
        # Setup: Create property, unit, and party
        property_obj = await DatabaseHelpers.create_property(db_session)
        unit_obj = await DatabaseHelpers.create_unit(db_session, property_obj.property_id)
        party_obj = await DatabaseHelpers.create_party(db_session)
        
        contract_data = TestDataFactory.create_contract_data(
            str(unit_obj.unit_id),
            str(party_obj.party_id)
        )
        
        response = await client.post("/api/v1/contracts", json=contract_data, headers=AUTH_HEADERS)
        APITestHelpers.assert_response_ok(response, 201)
        
        data = response.json()
        assert data["status"] == "active"
        assert data["unit_id"] == str(unit_obj.unit_id)
    
    @pytest.mark.asyncio
    async def test_get_contract(self, client: AsyncClient, db_session):
        """Test retrieving a contract."""
        # Setup
        property_obj = await DatabaseHelpers.create_property(db_session)
        unit_obj = await DatabaseHelpers.create_unit(db_session, property_obj.property_id)
        party_obj = await DatabaseHelpers.create_party(db_session)
        contract_obj = await DatabaseHelpers.create_contract(
            db_session,
            str(unit_obj.unit_id),
            str(party_obj.party_id)
        )
        
        response = await client.get(f"/api/v1/contracts/{contract_obj.contract_id}", headers=AUTH_HEADERS)
        APITestHelpers.assert_response_ok(response)
        
        data = response.json()
        assert data["contract_id"] == str(contract_obj.contract_id)
    
    @pytest.mark.asyncio
    async def test_list_contracts_by_property(self, client: AsyncClient, db_session):
        """Test listing contracts for a property."""
        property_obj = await DatabaseHelpers.create_property(db_session)
        unit_obj = await DatabaseHelpers.create_unit(db_session, property_obj.property_id)
        party_obj = await DatabaseHelpers.create_party(db_session)
        
        # Create multiple contracts
        await DatabaseHelpers.create_contract(db_session, str(unit_obj.unit_id), str(party_obj.party_id))
        await DatabaseHelpers.create_contract(db_session, str(unit_obj.unit_id), str(party_obj.party_id))
        
        response = await client.get(f"/api/v1/properties/{property_obj.property_id}/contracts", headers=AUTH_HEADERS)
        APITestHelpers.assert_response_ok(response)
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
    
    @pytest.mark.asyncio
    async def test_update_contract_status(self, client: AsyncClient, db_session):
        """Test updating contract status."""
        property_obj = await DatabaseHelpers.create_property(db_session)
        unit_obj = await DatabaseHelpers.create_unit(db_session, property_obj.property_id)
        party_obj = await DatabaseHelpers.create_party(db_session)
        contract_obj = await DatabaseHelpers.create_contract(
            db_session,
            str(unit_obj.unit_id),
            str(party_obj.party_id)
        )
        
        update_data = {"status": "terminated"}
        response = await client.patch(
            f"/api/v1/contracts/{contract_obj.contract_id}",
            json=update_data,
            headers=AUTH_HEADERS
        )
        APITestHelpers.assert_response_ok(response)
        
        data = response.json()
        assert data["status"] == "terminated"


@pytest.mark.integration
@pytest.mark.requires_db
class TestPartiesCRUD:
    """Tests for Parties CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_party(self, client: AsyncClient):
        """Test creating a new party."""
        party_data = TestDataFactory.create_party_data()
        
        response = await client.post("/api/v1/parties", json=party_data, headers=AUTH_HEADERS)
        APITestHelpers.assert_response_ok(response, 201)
        
        data = response.json()
        assert data["name"] == party_data["name"]
        assert data["orgnr"] == party_data["orgnr"]
    
    @pytest.mark.asyncio
    async def test_get_party_by_orgnr(self, client: AsyncClient, db_session):
        """Test retrieving party by organization number."""
        party_obj = await DatabaseHelpers.create_party(db_session, {"orgnr": "987654321", "name": "Existing Party AS"})
        
        response = await client.get(f"/api/v1/parties?orgnr={party_obj.orgnr}", headers=AUTH_HEADERS)
        APITestHelpers.assert_response_ok(response)
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["orgnr"] == party_obj.orgnr
    
    @pytest.mark.asyncio
    async def test_update_party(self, client: AsyncClient, db_session):
        """Test updating party information."""
        party_obj = await DatabaseHelpers.create_party(db_session)
        
        update_data = {"contact_email": "newemail@example.com"}
        response = await client.patch(
            f"/api/v1/parties/{party_obj.party_id}",
            json=update_data,
            headers=AUTH_HEADERS
        )
        APITestHelpers.assert_response_ok(response)
        
        data = response.json()
        assert data["contact_email"] == "newemail@example.com"


@pytest.mark.integration
@pytest.mark.requires_db
class TestUnitsCRUD:
    """Tests for Units CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_unit(self, client: AsyncClient, db_session):
        """Test creating a new unit."""
        property_obj = await DatabaseHelpers.create_property(db_session)
        unit_data = TestDataFactory.create_unit_data(str(property_obj.property_id))
        
        response = await client.post("/api/v1/units", json=unit_data, headers=AUTH_HEADERS)
        APITestHelpers.assert_response_ok(response, 201)
        
        data = response.json()
        assert data["property_id"] == str(property_obj.property_id)
        assert data["purpose"] == unit_data["purpose"]
    
    @pytest.mark.asyncio
    async def test_get_units_by_property(self, client: AsyncClient, db_session):
        """Test getting all units for a property."""
        property_obj = await DatabaseHelpers.create_property(db_session)
        
        # Create multiple units
        await DatabaseHelpers.create_unit(db_session, property_obj.property_id)
        await DatabaseHelpers.create_unit(db_session, property_obj.property_id)
        
        response = await client.get(f"/api/v1/properties/{property_obj.property_id}/units", headers=AUTH_HEADERS)
        APITestHelpers.assert_response_ok(response)
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
