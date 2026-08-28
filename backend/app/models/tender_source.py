"""Tender source and collection job models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import (
    CollectionErrorType,
    CollectionEventLevel,
    CollectionJobStatus,
    CollectionMethod,
    SourceHealthStatus,
    TenderSourceType,
)


class TenderSource(Base):
    __tablename__ = "tender_sources"
    __table_args__ = (
        Index("ix_tender_sources_code", "code", unique=True),
        Index("ix_tender_sources_state", "state"),
        Index("ix_tender_sources_is_active", "is_active"),
        Index("ix_tender_sources_health_status", "health_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    authority: Mapped[str | None] = mapped_column(String(255), nullable=True)
    portal_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_type: Mapped[TenderSourceType] = mapped_column(
        Enum(TenderSourceType, name="tender_source_type"),
        nullable=False,
    )
    collection_method: Mapped[CollectionMethod] = mapped_column(
        Enum(CollectionMethod, name="collection_method"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    configuration: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    health_status: Mapped[SourceHealthStatus] = mapped_column(
        Enum(SourceHealthStatus, name="source_health_status"),
        nullable=False,
        default=SourceHealthStatus.UNKNOWN,
        server_default=SourceHealthStatus.UNKNOWN.value,
    )
    last_collection_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_collection_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    collection_jobs: Mapped[list["TenderCollectionJob"]] = relationship(
        back_populates="tender_source",
        cascade="all, delete-orphan",
    )


class TenderCollectionJob(Base):
    __tablename__ = "tender_collection_jobs"
    __table_args__ = (
        Index("ix_tender_collection_jobs_source_id", "tender_source_id"),
        Index("ix_tender_collection_jobs_status", "status"),
        Index("ix_tender_collection_jobs_started_at", "started_at"),
        Index("ix_tender_collection_jobs_completed_at", "completed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[CollectionJobStatus] = mapped_column(
        Enum(CollectionJobStatus, name="collection_job_status"),
        nullable=False,
        default=CollectionJobStatus.QUEUED,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    records_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_skipped: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    records_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tender_source: Mapped[TenderSource] = relationship(back_populates="collection_jobs")
    events: Mapped[list["TenderCollectionEvent"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )
    raw_records: Mapped[list["TenderRawRecord"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )


class TenderCollectionEvent(Base):
    __tablename__ = "tender_collection_events"
    __table_args__ = (Index("ix_tender_collection_events_job_id", "job_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_collection_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    tender_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    level: Mapped[CollectionEventLevel] = mapped_column(
        Enum(CollectionEventLevel, name="collection_event_level"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    error_type: Mapped[CollectionErrorType | None] = mapped_column(
        Enum(CollectionErrorType, name="collection_error_type"),
        nullable=True,
    )
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job: Mapped[TenderCollectionJob] = relationship(back_populates="events")


class TenderRawRecord(Base):
    __tablename__ = "tender_raw_records"
    __table_args__ = (
        Index("ix_tender_raw_records_source_id", "tender_source_id"),
        Index("ix_tender_raw_records_source_tender_id", "source_tender_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_collection_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    tender_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_tender_id: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job: Mapped[TenderCollectionJob] = relationship(back_populates="raw_records")
