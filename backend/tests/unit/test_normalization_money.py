"""Unit tests for money normalization."""

from decimal import Decimal

from app.normalization.money import normalize_amount


def test_normalize_amount_indian_comma_format():
    parsed, original = normalize_amount("1,25,00,000")
    assert parsed == Decimal("12500000")
    assert original == "1,25,00,000"


def test_normalize_amount_plain_numeric():
    parsed, _ = normalize_amount("12500000")
    assert parsed == Decimal("12500000")


def test_normalize_amount_rupee_symbol():
    parsed, _ = normalize_amount("₹1,25,00,000")
    assert parsed == Decimal("12500000")


def test_normalize_amount_invalid_value():
    parsed, original = normalize_amount("two crore")
    assert parsed is None
    assert original == "two crore"


def test_normalize_amount_decimal_input():
    parsed, _ = normalize_amount(Decimal("100.50"))
    assert parsed == Decimal("100.50")
