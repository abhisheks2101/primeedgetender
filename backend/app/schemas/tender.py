"""Pydantic schemas for normalized tenders."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    DuplicateMatchType,
    DuplicateReviewStatus,
    IndianStateCode,
    NormalizationStatus,
    TenderStatus,
)


from app.schemas.tender_document import TenderDocumentSummary as TenderDocumentPublic


class TenderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tender_source_id: UUID
    source_tender_id: str
    reference_number: str | None = None
    title: str | None = None
    organization: str | None = None
    location: str | None = None
    state: str | None = None
    state_code: IndianStateCode
    status: TenderStatus
    normalization_status: NormalizationStatus
    submission_end: datetime | None = None
    estimated_value: Decimal | None = None


class TenderPublic(TenderSummary):
    work_description: str | None = None
    department: str | None = None
    tender_type: str | None = None
    tender_category: str | None = None
    district: str | None = None
    original_location_text: str | None = None
    emd_amount: Decimal | None = None
    tender_fee: Decimal | None = None
    publication_date: datetime | None = None
    document_sale_start: datetime | None = None
    document_sale_end: datetime | None = None
    submission_start: datetime | None = None
    opening_date: datetime | None = None
    source_status: str | None = None
    source_url: str | None = None
    source_last_updated: datetime | None = None
    normalization_version: int
    validation_warnings: list[str] | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    normalized_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    documents: list[TenderDocumentPublic] = []


class TenderDuplicateTenderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tender_source_id: UUID
    source_tender_id: str
    reference_number: str | None = None
    title: str | None = None
    organization: str | None = None
    state_code: IndianStateCode
    status: TenderStatus


class TenderDuplicateCandidatePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tender_id: UUID
    candidate_tender_id: UUID
    match_type: DuplicateMatchType
    confidence: float
    matched_fields: list[str] | None = None
    review_status: DuplicateReviewStatus
    created_at: datetime
    reviewed_at: datetime | None = None
    tender: TenderDuplicateTenderSummary | None = None
    candidate_tender: TenderDuplicateTenderSummary | None = None


class TenderDuplicateReviewUpdate(BaseModel):
    review_status: DuplicateReviewStatus = Field(
        description="Review decision: CONFIRMED_DUPLICATE, NOT_DUPLICATE, or IGNORED.",
    )
