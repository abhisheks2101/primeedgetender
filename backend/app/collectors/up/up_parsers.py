"""Isolated HTML parsers for the Uttar Pradesh NIC GeP portal."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup, Tag

from app.collectors.errors import ParsingCollectionError
from app.core.enums import TenderStatus

logger = logging.getLogger(__name__)

DATE_FORMATS = (
    "%d-%b-%Y %I:%M %p",
    "%d-%b-%Y %H:%M",
    "%d-%b-%Y",
    "%d/%m/%Y %I:%M %p",
    "%d/%m/%Y",
)

CAPTION_ALIASES = {
    "tender id": "tender_id",
    "tender reference number": "reference_number",
    "tender ref no": "reference_number",
    "reference number": "reference_number",
    "organisation chain": "organization",
    "organization chain": "organization",
    "tender title": "title",
    "work description": "work_description",
    "location": "location",
    "tender category": "tender_category",
    "tender type": "tender_type",
    "tender value in": "estimated_value",
    "tender value": "estimated_value",
    "emd amount in": "emd_amount",
    "emd amount": "emd_amount",
    "tender fee in": "tender_fee",
    "tender fee": "tender_fee",
    "published date": "publication_date",
    "document download / sale start date": "document_sale_start",
    "document download/sale start date": "document_sale_start",
    "document download / sale end date": "document_sale_end",
    "document download/sale end date": "document_sale_end",
    "bid submission start date": "submission_start",
    "bid submission end date": "submission_end",
    "tender opening date": "opening_date",
    "tender opening date & time": "opening_date",
}


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split()).strip()
    if not cleaned or cleaned.upper() in {"NA", "N/A", "-", "--"}:
        return None
    return cleaned


def _normalize_caption(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", value.lower()).strip()


def parse_dates(raw_value: str | None) -> tuple[datetime | None, str | None]:
    """Parse portal date strings into timezone-aware datetimes."""
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return None, raw_value

    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed, cleaned
        except ValueError:
            continue

    logger.warning("Unable to parse date value: %s", cleaned)
    return None, cleaned


def parse_amount(raw_value: str | None) -> tuple[Decimal | None, str | None]:
    """Parse Indian currency strings such as 1,25,00,000 into Decimal."""
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return None, raw_value

    normalized = cleaned.replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
    normalized = normalized.replace(",", "")
    if not normalized or not re.fullmatch(r"\d+(\.\d+)?", normalized):
        logger.warning("Unable to parse amount value: %s", cleaned)
        return None, cleaned

    try:
        return Decimal(normalized), cleaned
    except InvalidOperation:
        logger.warning("Invalid decimal amount: %s", cleaned)
        return None, cleaned


def parse_location(raw_value: str | None, default_state: str = "Uttar Pradesh") -> dict[str, str | None]:
    """Extract location fields while preserving original text."""
    cleaned = _clean_text(raw_value)
    district = None
    if cleaned and "," in cleaned:
        parts = [part.strip() for part in cleaned.split(",") if part.strip()]
        if parts:
            district = parts[0]
    return {
        "location": cleaned,
        "district": district,
        "state": default_state if cleaned else None,
        "location_raw": cleaned,
    }


def parse_status(
    submission_end: datetime | None,
    *,
    now: datetime | None = None,
    source_status: str | None = None,
) -> tuple[TenderStatus, str | None]:
    """Infer normalized status from submission end date when explicit status is absent."""
    preserved = _clean_text(source_status)
    if preserved:
        lowered = preserved.lower()
        if "cancel" in lowered:
            return TenderStatus.CANCELLED, preserved
        if "award" in lowered:
            return TenderStatus.AWARDED, preserved
        if "close" in lowered:
            return TenderStatus.CLOSED, preserved
        if "open" in lowered or "active" in lowered:
            return TenderStatus.OPEN, preserved

    if submission_end is None:
        return TenderStatus.UNKNOWN, preserved

    current = now or datetime.now(UTC)
    if submission_end.tzinfo is None:
        submission_end = submission_end.replace(tzinfo=UTC)

    if submission_end >= current:
        return TenderStatus.OPEN, preserved
    return TenderStatus.CLOSED, preserved


def _extract_sp_param(url: str) -> str | None:
    query = parse_qs(urlparse(url).query)
    values = query.get("sp")
    return values[0] if values else None


def parse_listing_page(html: str, base_url: str) -> list[dict[str, Any]]:
    """Parse the home page active tenders table."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="activeTenders")
    if table is None:
        raise ParsingCollectionError("Active tenders table (#activeTenders) not found on listing page.")

    summaries: list[dict[str, Any]] = []
    rows = table.find_all("tr")
    for row in rows[1:]:
        summary = parse_tender_summary(row, base_url)
        if summary is not None:
            summaries.append(summary)
    return summaries


def parse_tender_summary(row: Tag, base_url: str) -> dict[str, Any] | None:
    """Parse one listing row from the active tenders table."""
    cells = row.find_all("td")
    if len(cells) < 4:
        return None

    link = cells[0].find("a", href=True)
    if link is None:
        return None

    detail_url = urljoin(base_url, link["href"])
    source_tender_id = _extract_sp_param(detail_url)
    if not source_tender_id:
        source_tender_id = _clean_text(link.get_text()) or detail_url

    title = _clean_text(link.get_text())
    reference_number = _clean_text(cells[1].get_text())
    closing_raw = _clean_text(cells[2].get_text())
    opening_raw = _clean_text(cells[3].get_text())
    submission_end, submission_end_raw = parse_dates(closing_raw)
    opening_date, opening_date_raw = parse_dates(opening_raw)

    return {
        "source_tender_id": source_tender_id,
        "title": title,
        "reference_number": reference_number,
        "submission_end": submission_end.isoformat() if submission_end else None,
        "submission_end_raw": submission_end_raw,
        "opening_date": opening_date.isoformat() if opening_date else None,
        "opening_date_raw": opening_date_raw,
        "detail_url": detail_url,
        "listing_source": "activeTenders",
    }


def parse_tender_detail(html: str, detail_url: str) -> dict[str, Any]:
    """Parse a tender detail page into structured fields."""
    soup = BeautifulSoup(html, "html.parser")
    fields: dict[str, Any] = {"detail_url": detail_url, "field_map": {}}

    for row in soup.find_all("tr"):
        caption_cell = row.find("td", class_="td_caption")
        field_cell = row.find("td", class_="td_field")
        if caption_cell is None or field_cell is None:
            continue

        caption = _normalize_caption(caption_cell.get_text())
        key = CAPTION_ALIASES.get(caption)
        if key is None:
            continue

        raw_value = _clean_text(field_cell.get_text())
        fields["field_map"][key] = raw_value

        if key == "tender_id":
            fields["source_tender_id"] = raw_value
        elif key in {"title", "reference_number", "work_description", "organization", "tender_category", "tender_type"}:
            fields[key] = raw_value
        elif key in {"estimated_value", "emd_amount", "tender_fee"}:
            amount, amount_raw = parse_amount(raw_value)
            fields[key] = str(amount) if amount is not None else None
            fields[f"{key}_raw"] = amount_raw
        elif key.endswith("_date") or key in {
            "publication_date",
            "document_sale_start",
            "document_sale_end",
            "submission_start",
            "submission_end",
            "opening_date",
        }:
            parsed, raw = parse_dates(raw_value)
            fields[key] = parsed.isoformat() if parsed else None
            fields[f"{key}_raw"] = raw
        elif key == "location":
            fields.update(parse_location(raw_value))

    if not fields.get("source_tender_id"):
        fallback_id = _extract_sp_param(detail_url)
        if fallback_id:
            fields["source_tender_id"] = fallback_id

    if not fields.get("source_tender_id"):
        raise ParsingCollectionError("Tender detail page is missing a stable tender ID.")

    documents = parse_documents(html, detail_url)
    fields["documents"] = documents
    return fields


def parse_documents(html: str, base_url: str) -> list[dict[str, str | None]]:
    """Extract publicly linked tender document references."""
    soup = BeautifulSoup(html, "html.parser")
    documents: list[dict[str, str | None]] = []
    seen: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "docDownoad" not in href and "docDownload" not in href and "download" not in href.lower():
            continue
        document_url = urljoin(base_url, href)
        if document_url in seen:
            continue
        seen.add(document_url)
        document_name = _clean_text(link.get_text()) or "Tender Document"
        documents.append(
            {
                "document_id": document_name,
                "document_name": document_name,
                "document_url": document_url,
                "document_type": "notice" if "notice" in document_name.lower() else None,
            }
        )
    return documents
