"""Unit tests for MP portal HTML parsers."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from app.collectors.errors import ParsingCollectionError
from app.collectors.mp import mp_parsers
from app.core.enums import TenderStatus

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "mp"


def load_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_listing_page_discovers_multiple_tenders():
    html = load_fixture("home_listing.html")
    summaries = mp_parsers.parse_listing_page(html, "https://mptenders.gov.in/nicgep/app?page=Home&service=page")
    assert len(summaries) == 3
    assert summaries[0]["source_tender_id"] == "MP_OPEN_TOKEN_001"


def test_parse_listing_page_missing_table_raises():
    with pytest.raises(ParsingCollectionError):
        mp_parsers.parse_listing_page(load_fixture("malformed_listing.html"), "https://example.test")


def test_parse_tender_detail_open_tender():
    detail = mp_parsers.parse_tender_detail(load_fixture("tender_detail_open.html"), "https://example.test/detail")
    assert detail["source_tender_id"] == "2026_MP_100001_1"
    assert detail["title"] == "Road Construction Work in Bhopal"
    assert detail["estimated_value"] == "5000000"
    assert detail["emd_amount"] == "100000"
    assert len(detail["documents"]) == 2


def test_parse_tender_detail_handles_missing_fields():
    detail = mp_parsers.parse_tender_detail(load_fixture("tender_detail_closed.html"), "https://example.test/detail")
    assert detail["title"] == "Supply of Medical Equipment"
    assert detail.get("estimated_value") is None
    assert detail["documents"] == []


def test_parse_dates_valid_and_invalid():
    parsed, _ = mp_parsers.parse_dates("28-Aug-2026 12:30 PM")
    assert parsed is not None
    parsed_invalid, _ = mp_parsers.parse_dates("not-a-date")
    assert parsed_invalid is None


def test_parse_amount_indian_currency_and_invalid():
    amount, _ = mp_parsers.parse_amount("50,00,000")
    assert amount == Decimal("5000000")
    invalid, invalid_raw = mp_parsers.parse_amount("NA")
    assert invalid is None
    assert invalid_raw == "NA"


def test_parse_status_open_closed_unknown():
    future = datetime(2030, 1, 1, tzinfo=UTC)
    past = datetime(2020, 1, 1, tzinfo=UTC)
    assert mp_parsers.parse_status(future, now=datetime(2026, 1, 1, tzinfo=UTC))[0] == TenderStatus.OPEN
    assert mp_parsers.parse_status(past, now=datetime(2026, 1, 1, tzinfo=UTC))[0] == TenderStatus.CLOSED
    assert mp_parsers.parse_status(None)[0] == TenderStatus.UNKNOWN


def test_parse_documents_extracts_links():
    documents = mp_parsers.parse_documents(load_fixture("tender_detail_open.html"), "https://mptenders.gov.in/nicgep/app")
    assert len(documents) == 2
    assert documents[0]["document_name"] == "Tendernotice_1.pdf"
