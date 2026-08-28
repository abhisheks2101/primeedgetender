"""Unit tests for UP portal HTML parsers."""

from datetime import UTC, datetime
from decimal import Decimal

from pathlib import Path

import pytest

from app.collectors.errors import ParsingCollectionError
from app.collectors.up import up_parsers
from app.core.enums import TenderStatus

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "up"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_listing_page_discovers_multiple_tenders():
    html = load_fixture("home_listing.html")
    summaries = up_parsers.parse_listing_page(html, "https://etender.up.nic.in/nicgep/app?page=Home&service=page")
    assert len(summaries) == 3
    assert summaries[0]["source_tender_id"] == "2026_UPCDF_1178990_1"
    assert summaries[0]["title"] == "Supply of Medical Equipment"


def test_parse_listing_page_missing_table_raises():
    html = load_fixture("malformed_listing.html")
    with pytest.raises(ParsingCollectionError):
        up_parsers.parse_listing_page(html, "https://example.test")


def test_parse_tender_detail_open_tender():
    html = load_fixture("tender_detail_open.html")
    detail = up_parsers.parse_tender_detail(html, "https://example.test/detail-open")
    assert detail["source_tender_id"] == "2026_UPCDF_1178990_1"
    assert detail["title"] == "Supply of Medical Equipment"
    assert detail["estimated_value"] == "12500000"
    assert detail["emd_amount"] == "250000"
    assert len(detail["documents"]) == 1


def test_parse_tender_detail_handles_missing_fields():
    html = load_fixture("tender_detail_closed.html")
    detail = up_parsers.parse_tender_detail(html, "https://example.test/detail-closed")
    assert detail["title"] == "Road Repair Works"
    assert detail.get("estimated_value") is None
    assert detail["documents"] == []


def test_parse_dates_valid_and_invalid():
    parsed, raw = up_parsers.parse_dates("27-Aug-2026 06:55 PM")
    assert parsed is not None
    assert raw == "27-Aug-2026 06:55 PM"

    parsed_invalid, raw_invalid = up_parsers.parse_dates("invalid-date-value")
    assert parsed_invalid is None
    assert raw_invalid == "invalid-date-value"


def test_parse_amount_indian_currency_and_invalid():
    amount, raw = up_parsers.parse_amount("1,25,00,000")
    assert amount == Decimal("12500000")
    assert raw == "1,25,00,000"

    invalid, invalid_raw = up_parsers.parse_amount("NA")
    assert invalid is None
    assert invalid_raw == "NA"


def test_parse_status_open_closed_unknown():
    future = datetime(2030, 1, 1, tzinfo=UTC)
    past = datetime(2020, 1, 1, tzinfo=UTC)

    assert up_parsers.parse_status(future, now=datetime(2026, 1, 1, tzinfo=UTC))[0] == TenderStatus.OPEN
    assert up_parsers.parse_status(past, now=datetime(2026, 1, 1, tzinfo=UTC))[0] == TenderStatus.CLOSED
    assert up_parsers.parse_status(None)[0] == TenderStatus.UNKNOWN


def test_parse_documents_extracts_links():
    html = load_fixture("tender_detail_open.html")
    documents = up_parsers.parse_documents(html, "https://etender.up.nic.in/nicgep/app")
    assert len(documents) == 1
    assert documents[0]["document_name"] == "Tendernotice_1.pdf"
