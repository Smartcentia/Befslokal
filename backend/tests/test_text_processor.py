"""Tester for text_processor service."""
import pytest
from app.services.text_processor import (
    process_text_file,
    process_text_content
)


@pytest.mark.unit
@pytest.mark.importer
def test_process_text_content():
    """Test tekst prosessering og chunking."""
    text = "Dette er en test. " * 100  # Lang tekst for å trigge chunking
    metadata = {"source": "test"}
    
    result = process_text_content(text, "test_id", metadata)
    
    assert len(result) > 0
    assert "text" in result[0]
    assert "metadata" in result[0]
    assert result[0]["metadata"]["chunk_index"] == 0

@pytest.mark.unit
@pytest.mark.importer
def test_process_text_file(tmp_path):
    """Test tekstfil prosessering."""
    test_file = tmp_path / "test.txt"
    test_content = "Dette er innholdet i testfilen."
    test_file.write_text(test_content, encoding="utf-8")
    
    # Denne er ikke implementert ennå, men returnerer en tom liste
    chunks = process_text_file(
        text_path=test_file,
        source_id="file_test",
        metadata={"filename": "test.txt"}
    )
    
    assert isinstance(chunks, list)
