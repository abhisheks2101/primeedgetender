"""Pydantic schemas for tender source management."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.core.enums import (
    CollectionErrorType,
    CollectionEventLevel,
    CollectionJobStatus,
    CollectionMethod,
    SourceHealthStatus,
    TenderSourceType,
)


class SourceConfiguration(BaseModel):
    source_url: HttpUrl | None = None
    search_url: HttpUrl | None = None
    detail_url_pattern: str | None = Field(default=None, max_length=500)
    document_url_pattern: str | None = Field(default=None, max_length=500)
    request_timeout_seconds: float = Field(default=30.0, gt=0)
    retry_count: int = Field(default=3, ge=0)
    request_delay_seconds: float = Field(default=1.0, ge=0)
    max_requests_per_collection: int = Field(default=100, ge=1)
    pagination: dict | None = None

    @field_validator("detail_url_pattern", "document_url_pattern", mode="before")
    @classmethod
    def strip_patterns(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None


class TenderSourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=100, pattern=r"^[A-Z0-9_]+$")
    state: str | None = Field(default=None, max_length=120)
    authority: str | None = Field(default=None, max_length=255)
    portal_url: HttpUrl | None = None
    source_type: TenderSourceType
    collection_method: CollectionMethod
    priority: int = Field(default=100, ge=0)
    description: str | None = None
    configuration: SourceConfiguration = Field(default_factory=SourceConfiguration)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return str(value).strip().upper()


class TenderSourceCreate(TenderSourceBase):
    is_active: bool = True


class TenderSourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    state: str | None = Field(default=None, max_length=120)
    authority: str | None = Field(default=None, max_length=255)
    portal_url: HttpUrl | None = None
    source_type: TenderSourceType | None = None
    collection_method: CollectionMethod | None = None
    priority: int | None = Field(default=None, ge=0)
    description: str | None = None
    configuration: SourceConfiguration | None = None
    is_active: bool | None = None
    health_status: SourceHealthStatus | None = None


class TenderSourceStatusUpdate(BaseModel):
    is_active: bool
    health_status: SourceHealthStatus | None = None


class TenderSourceSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    state: str | None = None
    authority: str | None = None
    source_type: TenderSourceType
    collection_method: CollectionMethod
    is_active: bool
    health_status: SourceHealthStatus
    priority: int
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error: str | None = None


class TenderSourcePublic(TenderSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    health_status: SourceHealthStatus
    last_collection_started_at: datetime | None = None
    last_collection_completed_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime
    updated_at: datetime


class CollectionJobSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tender_source_id: UUID
    source_name: str | None = None
    source_code: str | None = None
    status: CollectionJobStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    records_discovered: int
    records_processed: int
    records_created: int
    records_updated: int
    records_skipped: int
    records_failed: int
    duration_seconds: float | None = None
    error_message: str | None = None
    created_at: datetime


class CollectionJobPublic(CollectionJobSummary):
    events: list["CollectionEventPublic"] = Field(default_factory=list)


class CollectionEventPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    level: CollectionEventLevel
    message: str
    error_type: CollectionErrorType | None = None
    context: dict | None = None
    created_at: datetime


class MessageResponse(BaseModel):
    message: str
