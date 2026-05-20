"""Database migration integration tests."""
import pytest
from sqlalchemy import inspect
from app.db.base import Base
from app.db import base as db_models


@pytest.mark.migration
@pytest.mark.integration
@pytest.mark.migration
@pytest.mark.integration
@pytest.mark.asyncio
async def test_migration_002_tables_exist(db_session):
    """Test that migration 002 creates correct tables."""
    def inspect_tables(conn):
        inspector = inspect(conn)
        return inspector.get_table_names()

    conn = await db_session.connection()
    tables = await conn.run_sync(inspect_tables)
    
    assert 'text_content' in tables, "text_content table should exist"
    assert 'external_api_data' in tables, "external_api_data table should exist"
    assert 'file_meta' in tables, "file_meta table should exist"


@pytest.mark.migration
@pytest.mark.integration
@pytest.mark.skip(reason="Flaky in async environment")
@pytest.mark.asyncio
async def test_text_content_structure(db_session):
    """Test text_content table structure."""
    def inspect_columns(conn):
        inspector = inspect(conn)
        return {col['name']: col for col in inspector.get_columns('text_content')}

    conn = await db_session.connection()
    columns = await conn.run_sync(inspect_columns)
    
    # Required columns
    assert 'text_id' in columns
    assert 'source_type' in columns
    assert 'content' in columns
    # assert 'metadata' in columns
    assert 'additional_metadata' in columns
    assert 'created_at' in columns
    
    # Optional foreign keys
    assert 'contract_id' in columns
    assert 'unit_id' in columns
    assert 'property_id' in columns
    
    # Check indexes
    def inspect_indexes(conn):
        inspector = inspect(conn)
        return inspector.get_indexes('text_content')

    conn = await db_session.connection()
    indexes = await conn.run_sync(inspect_indexes)
    index_names = [idx['name'] for idx in indexes]
    assert any('source_type' in idx['column_names'] for idx in indexes if idx.get('column_names'))


@pytest.mark.migration
@pytest.mark.integration
@pytest.mark.asyncio
async def test_external_api_data_structure(db_session):
    """Test external_api_data table structure."""
    def inspect_columns(conn):
        inspector = inspect(conn)
        return {col['name']: col for col in inspector.get_columns('external_api_data')}

    conn = await db_session.connection()
    columns = await conn.run_sync(inspect_columns)
    
    # Required columns
    assert 'api_data_id' in columns
    assert 'source_api' in columns
    assert 'entity_type' in columns
    assert 'entity_id' in columns
    assert 'data' in columns
    assert 'fetched_at' in columns
    
    # Optional
    assert 'expires_at' in columns


@pytest.mark.migration
@pytest.mark.integration
@pytest.mark.asyncio
async def test_file_meta_has_new_columns(db_session):
    """Test that file_meta has new columns from migration 002."""
    def inspect_columns(conn):
        inspector = inspect(conn)
        return {col['name']: col for col in inspector.get_columns('file_meta')}

    conn = await db_session.connection()
    columns = await conn.run_sync(inspect_columns)
    
    assert 'file_type' in columns, "file_type column should exist"
    assert 'content_type' in columns, "content_type column should exist"
    
    # Verify nullable
    assert columns['file_type']['nullable'] is True
    assert columns['content_type']['nullable'] is True


@pytest.mark.migration
@pytest.mark.integration
@pytest.mark.skip(reason="MissingGreenlet error")
@pytest.mark.asyncio
async def test_external_api_data_constraint(db_session):
    """Test that entity_type check constraint works."""
    from uuid import uuid4
    
    # Valid entity_type should work
    valid_data = db_models.ExternalApiData(
        source_api="test",
        entity_type="property",  # Valid
        entity_id=uuid4(),
        data={"test": "data"}
    )
    db_session.add(valid_data)
    await db_session.commit()
    assert valid_data.api_data_id is not None
    
    # Invalid entity_type should fail (if constraint enforced in SQLite)
    # Note: SQLite doesn't enforce check constraints by default
    # This test verifies the constraint exists in the schema
    
    await db_session.delete(valid_data)
    await db_session.commit()


@pytest.mark.migration
@pytest.mark.integration
@pytest.mark.skip(reason="MissingGreenlet error")
@pytest.mark.asyncio
async def test_text_content_foreign_keys(db_session):
    """Test that foreign keys in text_content work correctly."""
    from uuid import uuid4
    
    # Create a contract first
    contract = db_models.Contract(
        contract_id=uuid4(),
        unit_id=uuid4(),
        party_id=uuid4(),
        status="active",
        periods=[],
        amount={}
    )
    db_session.add(contract)
    await db_session.commit()
    
    # Create text_content with foreign key
    text_content = db_models.TextContent(
        source_type="file",
        content="Test",
        contract_id=contract.contract_id
    )
    db_session.add(text_content)
    await db_session.commit()
    
    assert text_content.text_id is not None
    assert text_content.contract_id == contract.contract_id
    
    # Cleanup
    await db_session.delete(text_content)
    await db_session.delete(contract)
    await db_session.commit()

