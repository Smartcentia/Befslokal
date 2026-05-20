"""
Unit tests for PDF processor with Docling integration.
Tests Docling extraction, PyPDF fallback, table extraction, and chunking.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from app.services.pdf_processor import (
    extract_text_from_pdf_pypdf,
    extract_text_from_pdf,
    chunk_text,
    process_pdf
)


class TestPyPDFExtraction:
    """Test PyPDF fallback extraction."""
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'PDF content')
    @patch('app.services.pdf_processor.Path')
    @patch('app.services.pdf_processor.pypdf')
    def test_extract_text_from_pdf_pypdf(self, mock_pypdf, mock_path_class, mock_file):
        """Test PyPDF text extraction."""
        # Mock file existence
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.name = "test.pdf"
        mock_path_class.return_value = mock_path
        
        # Setup mock
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 text"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 text"
        
        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pypdf.PdfReader.return_value = mock_reader
        
        # Test
        result = extract_text_from_pdf_pypdf("test.pdf")
        
        assert "Page 1 text" in result
        assert "Page 2 text" in result


class TestExtractTextFromPDF:
    """Test main extraction function with fallback logic."""
    
    @patch('app.services.pdf_processor.Path')
    @patch('app.services.pdf_processor.settings')
    @patch('app.services.pdf_processor.extract_text_from_pdf_pypdf')
    def test_extract_with_docling_disabled(self, mock_pypdf, mock_settings, mock_path_class):
        """Test extraction uses PyPDF when Docling is disabled."""
        # Mock file existence
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path_class.return_value = mock_path
        
        mock_settings.USE_DOCLING = False
        mock_pypdf.return_value = "PyPDF text"
        
        result = extract_text_from_pdf("test.pdf")
        
        assert result['source'] == 'pypdf'
        assert result['text'] == 'PyPDF text'
        assert result['tables'] == []
        mock_pypdf.assert_called_once()


class TestChunkText:
    """Test text chunking functionality."""
    
    def test_chunk_small_text(self):
        """Test chunking of small text."""
        text = "This is a small text."
        chunks = chunk_text(text, chunk_size=1000)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_chunk_large_text(self):
        """Test chunking of large text."""
        # Create text larger than chunk size
        text = " ".join(["word"] * 500)  # ~2500 chars
        chunks = chunk_text(text, chunk_size=1000, chunk_overlap=100)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 1200  # Allow some overflow
    
    def test_chunk_empty_text(self):
        """Test chunking of empty text."""
        chunks = chunk_text("")
        assert chunks == []


class TestProcessPDF:
    """Test complete PDF processing pipeline."""
    
    @patch('app.services.pdf_processor.extract_text_from_pdf')
    @patch('app.services.pdf_processor.chunk_text')
    def test_process_pdf_with_tables(self, mock_chunk, mock_extract):
        """Test PDF processing with table extraction."""
        mock_extract.return_value = {
            'text': 'Test content',
            'tables': [{'data': 'table1'}, {'data': 'table2'}],
            'metadata': {'title': 'Test'},
            'source': 'docling'
        }
        mock_chunk.return_value = ['chunk1', 'chunk2']
        
        result = process_pdf("test.pdf", "contract123", "file456")
        
        assert len(result) == 2
        assert result[0]['text'] == 'chunk1'
        assert result[0]['chunk_index'] == 0
        assert result[0]['source'] == 'docling'
        assert 'tables' in result[0]
        assert len(result[0]['tables']) == 2
        assert 'pdf_metadata' in result[0]
        assert result[0]['pdf_metadata']['title'] == 'Test'
        
        # Second chunk should not have tables/metadata
        assert 'tables' not in result[1]
        assert 'pdf_metadata' not in result[1]
    
    @patch('app.services.pdf_processor.extract_text_from_pdf')
    @patch('app.services.pdf_processor.chunk_text')
    def test_process_pdf_pypdf_fallback(self, mock_chunk, mock_extract):
        """Test PDF processing with PyPDF fallback."""
        mock_extract.return_value = {
            'text': 'PyPDF content',
            'tables': [],
            'metadata': {},
            'source': 'pypdf'
        }
        mock_chunk.return_value = ['chunk1']
        
        result = process_pdf("test.pdf", "contract123", "file456")
        
        assert len(result) == 1
        assert result[0]['source'] == 'pypdf'
        # Tables key should not be present if empty
        assert 'tables' not in result[0]
