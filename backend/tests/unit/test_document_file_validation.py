"""Unit tests for tender document file validation."""

from tests.document_fixtures import make_fake_pdf_html_bytes, make_pdf_bytes, make_txt_bytes
from app.document_processing.file_validation import validate_file_content


def test_validate_real_pdf():
    result = validate_file_content(make_pdf_bytes(["Page one text"]), claimed_extension="pdf")
    assert result.is_valid
    assert result.detected_type == "pdf"


def test_validate_html_pretending_to_be_pdf():
    result = validate_file_content(make_fake_pdf_html_bytes(), claimed_extension="pdf")
    assert not result.is_valid
    assert result.error_code.value == "INVALID_FILE"


def test_validate_txt_file():
    result = validate_file_content(make_txt_bytes("Average annual turnover requirement"), claimed_extension="txt")
    assert result.is_valid
    assert result.detected_type == "txt"


def test_validate_rejects_executable():
    result = validate_file_content(b"MZ" + b"\x00" * 100, claimed_extension="pdf")
    assert not result.is_valid
    assert result.error_code.value == "UNSUPPORTED_FILE"
