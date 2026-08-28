"""Unit tests for PDF text extraction."""

from tests.document_fixtures import make_pdf_bytes
from app.document_processing.extractors.pdf import extract_pdf_text


def test_extract_multi_page_pdf_preserves_pages():
    result = extract_pdf_text(make_pdf_bytes(["Page one content", "Page two content"]))
    assert result.success
    assert result.page_count == 2
    assert result.pages[0].page_number == 1
    assert result.pages[1].page_number == 2
    assert "Page one" in result.pages[0].text
    assert "Page two" in result.pages[1].text


def test_extract_empty_pdf_marks_ocr_need():
    result = extract_pdf_text(make_pdf_bytes([""]))
    assert result.success
    assert result.needs_ocr is True
