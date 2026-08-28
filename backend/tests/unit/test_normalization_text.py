"""Unit tests for text normalization."""

from app.normalization.text import normalize_reference, normalize_text


def test_normalize_text_trims_and_collapses_whitespace():
    assert normalize_text(" Road Construction Work ") == "road construction work"


def test_normalize_text_casefolds_for_comparison():
    assert normalize_text("ROAD CONSTRUCTION WORK") == normalize_text("road construction work")


def test_normalize_text_handles_unicode():
    assert normalize_text("Café  Road") == "café road"


def test_normalize_text_empty_values():
    assert normalize_text(None) is None
    assert normalize_text("   ") is None


def test_normalize_reference_strips_formatting():
    assert normalize_reference("TND/2026-001") == "tnd2026001"
