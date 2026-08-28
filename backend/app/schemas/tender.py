"""Pydantic schemas for normalized tenders."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import TenderStatus


class TenderDocumentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_name: str
    document_url: str | None = None
    document_type: str | None = None
    source_reference: str | None = None


class TenderSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tender_source_id: UUID
    source_tender_id: str
    reference_number: str | None = None
    title: str | None = None
    organization: str | None = None
    location: str | None = None
    status: TenderStatus
    submission_end: datetime | None = None
    estimated_value: Decimal | None = None


class TenderPublic(TenderSummary):
    work_description: str | None = None
    department: str | None = None
    tender_type: str | None = None
    tender_category: str | None = None
    district: str | None = None
    state: str | None = None
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
    created_at: datetime
    updated_at: datetime
    documents: list[TenderDocumentPublic] = []
