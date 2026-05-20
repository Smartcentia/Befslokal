import pytest
from httpx import AsyncClient
from unittest.mock import Mock, patch
from app.models.file_meta import FileMeta
from sqlalchemy import select

@pytest.mark.asyncio
async def test_upload_file_with_tags(client: AsyncClient, db_session):
    # Mock Storage
    with patch("app.api.v1.files.get_storage") as mock_storage_get:
        mock_storage = Mock()
        mock_storage.save_file.return_value = "uploads/test.pdf"
        mock_storage_get.return_value = mock_storage
        
        # Mock Indexer
        with patch("app.api.v1.files.index_pdf_file_async") as mock_indexer:
            mock_indexer.return_value = {"status": "mocked"}
            
            # Form Data
            files = {"file": ("test.pdf", b"pdf content", "application/pdf")}
            # httpx handles list of values for same key correctly for multipart
            data = {"tags": ["ai_colleague", "internal_control"]}
            
            response = await client.post(
                "/api/v1/files/upload",
                files=files,
                data=data
            )
            
            assert response.status_code == 201, response.text
            
            # Verify DB
            result = await db_session.execute(select(FileMeta).where(FileMeta.path == "uploads/test.pdf"))
            file_meta = result.scalar_one()
            
            assert file_meta.tags is not None
            assert "ai_colleague" in file_meta.tags
            assert "internal_control" in file_meta.tags
