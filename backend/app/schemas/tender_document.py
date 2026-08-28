"""Pydantic schemas for tender documents."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    TenderDocumentClassification,
    TenderDocumentDownloadStatus,
    TenderDocumentErrorCode,
    TenderDocumentExtractionMethod,
    TenderDocumentExtractionStatus,
    TenderDocumentProcessingEventKind,
    TenderDocumentProcessingJobStatus,
    TenderDocumentProcessingStatus,
)


class TenderDocumentPagePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    page_number: int
    text: str
    extraction_method: TenderDocumentExtractionMethod
    character_count: int


class TenderDocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tender_id: UUID
    source_document_id: str
    document_name: str
    document_url: str | None = None
    classification: TenderDocumentClassification
    download_status: TenderDocumentDownloadStatus
    processing_status: TenderDocumentProcessingStatus
    extraction_status: TenderDocumentExtractionStatus
    extraction_method: TenderDocumentExtractionMethod
    mime_type: str | None = None
    file_extension: str | None = None
    file_size: int | None = None
    checksum: str | None = None
    page_count: int | None = None
    character_count: int | None = None
    error_code: TenderDocumentErrorCode | None = None
    error_message: str | None = None
    downloaded_at: datetime | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TenderDocumentPublic(TenderDocumentSummary):
    document_type: str | None = None
    local_storage_path: str | None = None
    text_storage_path: str | None = None
    previous_checksum: str | None = None
    first_seen_at: datetime | None = None
    pages: list[TenderDocumentPagePublic] = []


class TenderDocumentProcessRequest(BaseModel):
    force: bool = Field(default=False, description="Reprocess even if already completed successfully.")


class TenderDocumentProcessingEventPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID | None = None
    kind: TenderDocumentProcessingEventKind
    message: str
    created_at: datetime


class TenderDocumentProcessingJobPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tender_id: UUID
    status: TenderDocumentProcessingJobStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    discovered: int
    downloaded: int
    skipped: int
    failed: int
    extracted: int
    ocr_processed: int
    error_message: str | None = None
    duration_seconds: float | None = None
    created_at: datetime
    events: list[TenderDocumentProcessingEventPublic] = []
