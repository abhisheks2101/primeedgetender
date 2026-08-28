"""Unit tests for tender identity resolution."""

import pytest

from app.normalization.identity import resolve_identity_key


def test_identity_same_source_and_id():
    key = resolve_identity_key(source_code="UP_TENDER", source_tender_id="123", reference_number=None)
    assert key == "UP_TENDER:123"


def test_identity_reference_fallback():
    key = resolve_identity_key(source_code="UP_TENDER", source_tender_id="", reference_number="TND/001")
    assert key == "UP_TENDER:ref:tnd001"


def test_identity_missing_both_raises():
    with pytest.raises(ValueError):
        resolve_identity_key(source_code="UP_TENDER", source_tender_id="", reference_number=None)
