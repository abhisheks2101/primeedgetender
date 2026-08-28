"""Unit tests for location and state normalization."""

from app.core.enums import IndianStateCode
from app.normalization.location import normalize_location, normalize_state


def test_normalize_state_up_variations():
    code, display = normalize_state("U.P.")
    assert code == IndianStateCode.UTTAR_PRADESH
    assert display == "Uttar Pradesh"


def test_normalize_state_mp_variations():
    code, _ = normalize_state("Madhya Pradesh")
    assert code == IndianStateCode.MADHYA_PRADESH


def test_normalize_state_unknown():
    code, _ = normalize_state("Karnataka")
    assert code == IndianStateCode.UNKNOWN


def test_normalize_state_from_source_code():
    code, _ = normalize_state(None, source_code="UP_TENDER")
    assert code == IndianStateCode.UTTAR_PRADESH


def test_normalize_location_preserves_original_text():
    data = normalize_location("Lucknow, Uttar Pradesh", source_code="UP_TENDER")
    assert data["original_location_text"] == "Lucknow, Uttar Pradesh"
    assert data["state_code"] == IndianStateCode.UTTAR_PRADESH
