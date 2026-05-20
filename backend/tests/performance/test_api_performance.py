"""Performance tests for API endpoints."""
import pytest
import time
from httpx import AsyncClient


@pytest.mark.performance
@pytest.mark.slow
class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    @pytest.mark.asyncio
    async def test_properties_list_performance(self, client: AsyncClient, db_session):
        """Test properties list endpoint performance."""
        from tests.helpers import DatabaseHelpers
        
        # Create 100 properties
        for i in range(100):
            await DatabaseHelpers.create_property(
                db_session, 
                {"address": f"Test Address {i}"}
            )
        
        # Measure response time
        start_time = time.time()
        response = await client.get("/api/v1/properties?limit=100")
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 1.0, f"Response took {elapsed_time}s, expected < 1s"
        
        data = response.json()
        assert len(data) == 100
    
    @pytest.mark.asyncio
    async def test_property_creation_performance(self, client: AsyncClient):
        """Test property creation endpoint performance."""
        from tests.helpers import TestDataFactory
        
        property_data = TestDataFactory.create_property_data()
        
        # Measure response time
        start_time = time.time()
        response = await client.post("/api/v1/properties", json=property_data)
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 201
        assert elapsed_time < 0.5, f"Response took {elapsed_time}s, expected < 0.5s"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, client: AsyncClient, db_session):
        """Test handling of concurrent requests."""
        import asyncio
        from tests.helpers import DatabaseHelpers
        
        # Create test data
        property_obj = await DatabaseHelpers.create_property(db_session)
        
        # Make 10 concurrent requests
        async def make_request():
            return await client.get(f"/api/v1/properties/{property_obj.property_id}")
        
        start_time = time.time()
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        elapsed_time = time.time() - start_time
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # Should handle concurrency efficiently
        assert elapsed_time < 2.0, f"Concurrent requests took {elapsed_time}s, expected < 2s"
    
    @pytest.mark.asyncio
    async def test_search_performance(self, client: AsyncClient, db_session):
        """Test search endpoint performance with many results."""
        from tests.helpers import DatabaseHelpers
        
        # Create 50 properties in Oslo
        for i in range(50):
            await DatabaseHelpers.create_property(
                db_session,
                {"address": f"Osloveien {i}", "city": "Oslo"}
            )
        
        # Search for Oslo properties
        start_time = time.time()
        response = await client.get("/api/v1/properties?city=Oslo")
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 1.0, f"Search took {elapsed_time}s, expected < 1s"
        
        data = response.json()
        assert len(data) == 50


@pytest.mark.performance
@pytest.mark.slow
class TestDatabasePerformance:
    """Performance tests for database queries."""
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, db_session):
        """Test bulk insert performance."""
        from app.domains.core.models.property import Property
        
        # Create 100 properties
        properties = [
            Property(
                address=f"Address {i}",
                postal_code="0001",
                city="Oslo",
                latitude=59.9139,
                longitude=10.7522,
            )
            for i in range(100)
        ]
        
        start_time = time.time()
        db_session.add_all(properties)
        await db_session.commit()
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 2.0, f"Bulk insert took {elapsed_time}s, expected < 2s"
    
    @pytest.mark.asyncio
    async def test_complex_query_performance(self, db_session):
        """Test performance of complex queries with joins."""
        from tests.helpers import DatabaseHelpers
        from sqlalchemy import select
        from app.domains.core.models.property import Property
        from app.domains.core.models.unit import Unit
        from app.domains.core.models.contract import Contract
        
        # Create test data with relationships
        property_obj = await DatabaseHelpers.create_property(db_session)
        unit_obj = await DatabaseHelpers.create_unit(db_session, property_obj.property_id)
        party_obj = await DatabaseHelpers.create_party(db_session)
        await DatabaseHelpers.create_contract(
            db_session,
            str(unit_obj.unit_id),
            str(party_obj.party_id)
        )
        
        # Complex query with joins
        start_time = time.time()
        query = (
            select(Property)
            .join(Unit, Unit.property_id == Property.property_id)
            .join(Contract, Contract.unit_id == Unit.unit_id)
        )
        result = await db_session.execute(query)
        result.scalars().all()
        elapsed_time = time.time() - start_time
        
        assert elapsed_time < 0.5, f"Complex query took {elapsed_time}s, expected < 0.5s"
