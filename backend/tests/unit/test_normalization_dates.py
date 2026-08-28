"""Unit tests for date normalization."""

from datetime import UTC, datetime

from app.normalization.dates import normalize_datetime


def test_normalize_datetime_up_format():
    parsed, original = normalize_datetime("15-Sep-2026 04:30 PM")
    assert parsed is not None
    assert parsed.tzinfo == UTC
    assert original == "15-Sep-2026 04:30 PM"


def test_normalize_datetime_mp_slash_format():
    parsed, _ = normalize_datetime("15/09/2026")
    assert parsed is not None
    assert parsed.day == 15


def test_normalize_datetime_invalid_format():
    parsed, original = normalize_datetime("not-a-date")
    assert parsed is None
    assert original == "not-a-date"


def test_normalize_datetime_missing_value():
    parsed, original = normalize_datetime(None)
    assert parsed is None
    assert original is None


def test_normalize_datetime_preserves_existing_datetime():
    value = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
    parsed, original = normalize_datetime(value)
    assert parsed == value
    assert original == value.isoformat()
