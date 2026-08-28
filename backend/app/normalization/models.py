"""Normalized tender payload produced by the Module 7 pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.core.enums import IndianStateCode, NormalizationStatus, TenderStatus


@dataclass(slots=True)
class NormalizedTenderPayload:
    source_tender_id: str
    reference_number: str | None = None
    title: str | None = None
    work_description: str | None = None
    organization: str | None = None
    department: str | None = None
    tender_type: str | None = None
    tender_category: str | None = None
    location: str | None = None
    district: str | None = None
    state: str | None = None
    state_code: IndianStateCode = IndianStateCode.UNKNOWN
    original_location_text: str | None = None
    estimated_value: Decimal | None = None
    emd_amount: Decimal | None = None
    tender_fee: Decimal | None = None
    publication_date: datetime | None = None
    document_sale_start: datetime | None = None
    document_sale_end: datetime | None = None
    submission_start: datetime | None = None
    submission_end: datetime | None = None
    opening_date: datetime | None = None
    status: TenderStatus = TenderStatus.UNKNOWN
    source_status: str | None = None
    source_url: str | None = None
    source_last_updated: datetime | None = None
    title_normalized: str | None = None
    description_normalized: str | None = None
    organization_normalized: str | None = None
    normalization_version: int = 1
    normalization_status: NormalizationStatus = NormalizationStatus.NORMALIZED
    validation_warnings: list[str] = field(default_factory=list)
