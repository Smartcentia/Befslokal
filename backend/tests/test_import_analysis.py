
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.csv_importer import analyze_import

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_analyze_import_party_new_fields(mock_db_session):
    """Test analysis of CSV with new fields."""
    csv_content = b"orgnr,name,custom_field\n123456789,Test Party,Value1"
    
    # Mock _get_model_fields to return standard fields
    with patch("app.services.csv_importer._get_model_fields") as mock_get_fields:
        mock_get_fields.return_value = ["orgnr", "name"]
        
        # Mock query result
        # Configure mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        
        result = await analyze_import(csv_content, "party", mock_db_session)
        
        assert result["total_rows"] == 1
        assert "custom_field" in result["new_columns"]
        assert len(result["new_records"]) == 1
        assert result["new_records"][0]["custom_field"] == "Value1"

@pytest.mark.asyncio
async def test_analyze_import_conflict(mock_db_session):
    """Test conflict detection."""
    csv_content = b"orgnr,name\n999999999,New Name"
    
    with patch("app.services.csv_importer._get_model_fields") as mock_get_fields:
        mock_get_fields.return_value = ["orgnr", "name"]
        
        # Mock existing party record match
        mock_existing = MagicMock()
        mock_existing.orgnr = "999999999"
        mock_existing.name = "Old Name"
        mock_existing.external_data = {}
        # Make sure getattr works for mocking
        
        # Configure mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_existing
        mock_db_session.execute.return_value = mock_result

        
        result = await analyze_import(csv_content, "party", mock_db_session)
        
        assert len(result["conflicts"]) == 1
        conflict = result["conflicts"][0]
        assert conflict["row_key"] == 999999999
        assert conflict["diffs"]["name"]["db"] == "Old Name"
        assert conflict["diffs"]["name"]["csv"] == "New Name"
