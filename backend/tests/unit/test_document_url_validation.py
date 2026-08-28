"""Unit tests for document URL validation and SSRF protection."""

import pytest

from app.document_processing.url_validation import URLValidationError, validate_document_url


def test_validate_document_url_allows_configured_domain():
    url = validate_document_url("https://example.test/tender.pdf", allowed_domains=["example.test"])
    assert url.endswith("tender.pdf")


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/tender.pdf",
        "http://127.0.0.1/tender.pdf",
        "http://192.168.1.10/tender.pdf",
        "http://10.0.0.5/tender.pdf",
    ],
)
def test_validate_document_url_rejects_private_targets(url):
    with pytest.raises(URLValidationError):
        validate_document_url(url, allowed_domains=["example.test"])


def test_validate_document_url_rejects_unknown_domain():
    with pytest.raises(URLValidationError):
        validate_document_url("https://evil.example/tender.pdf", allowed_domains=["example.test"])
