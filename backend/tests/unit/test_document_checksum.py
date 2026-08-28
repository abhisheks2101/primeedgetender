"""Unit tests for checksum helpers."""

from tests.document_fixtures import make_pdf_bytes
from app.document_processing.checksum import sha256_checksum


def test_same_file_same_checksum():
    content = make_pdf_bytes(["Checksum test"])
    assert sha256_checksum(content) == sha256_checksum(content)


def test_changed_file_different_checksum():
    first = make_pdf_bytes(["Version one"])
    second = make_pdf_bytes(["Version two"])
    assert sha256_checksum(first) != sha256_checksum(second)
