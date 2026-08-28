"""Normalized tender and document models."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import DuplicateMatchType, DuplicateReviewStatus, IndianStateCode, NormalizationStatus, TenderStatus


class Tender(Base):
    __tablename__ = "tenders"
    __table_args__ = (
        UniqueConstraint("tender_source_id", "source_tender_id", name="uq_tenders_source_tender_id"),
        Index("ix_tenders_source_id", "tender_source_id"),
        Index("ix_tenders_status", "status"),
        Index("ix_tenders_reference_number", "reference_number"),
        Index("ix_tenders_submission_end", "submission_end"),
        Index("ix_tenders_state_code", "state_code"),
        Index("ix_tenders_organization", "organization"),
        Index("ix_tenders_department", "department"),
        Index("ix_tenders_normalization_status", "normalization_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tender_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_tender_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    work_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    organization: Mapped[str | None] = mapped_column(String(500), nullable=True)
    department: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tender_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tender_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    district: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state_code: Mapped[IndianStateCode] = mapped_column(
        Enum(IndianStateCode, name="indian_state_code"),
        nullable=False,
        default=IndianStateCode.UNKNOWN,
        server_default=IndianStateCode.UNKNOWN.value,
    )
    original_location_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    title_normalized: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    description_normalized: Mapped[str | None] = mapped_column(Text, nullable=True)
    organization_normalized: Mapped[str | None] = mapped_column(String(500), nullable=True)
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    emd_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    tender_fee: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    document_sale_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    document_sale_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submission_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submission_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opening_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[TenderStatus] = mapped_column(
        Enum(TenderStatus, name="tender_status"),
        nullable=False,
        default=TenderStatus.UNKNOWN,
    )
    source_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    normalization_version: Mapped[int] = mapped_column(nullable=False, default=1, server_default="1")
    normalization_status: Mapped[NormalizationStatus] = mapped_column(
        Enum(NormalizationStatus, name="normalization_status"),
        nullable=False,
        default=NormalizationStatus.NOT_PROCESSED,
        server_default=NormalizationStatus.NOT_PROCESSED.value,
    )
    validation_warnings: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    normalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    documents: Mapped[list["TenderDocument"]] = relationship(
        back_populates="tender",
        cascade="all, delete-orphan",
    )
    change_history: Mapped[list["TenderChangeHistory"]] = relationship(
        back_populates="tender",
        cascade="all, delete-orphan",
    )
    duplicate_candidates: Mapped[list["TenderDuplicateCandidate"]] = relationship(
        back_populates="tender",
        foreign_keys="TenderDuplicateCandidate.tender_id",
        cascade="all, delete-orphan",
    )


class TenderChangeHistory(Base):
    __tablename__ = "tender_change_history"
    __table_args__ = (Index("ix_tender_change_history_tender_id", "tender_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False)
    field_name: Mapped[str] = mapped_column(String(120), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tender: Mapped[Tender] = relationship(back_populates="change_history")


class TenderDuplicateCandidate(Base):
    __tablename__ = "tender_duplicate_candidates"
    __table_args__ = (
        UniqueConstraint("tender_id", "candidate_tender_id", name="uq_tender_duplicate_pair"),
        Index("ix_tender_duplicate_candidates_status", "review_status"),
        Index("ix_tender_duplicate_candidates_match_type", "match_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False)
    candidate_tender_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False)
    match_type: Mapped[DuplicateMatchType] = mapped_column(
        Enum(DuplicateMatchType, name="duplicate_match_type"),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(nullable=False)
    matched_fields: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    review_status: Mapped[DuplicateReviewStatus] = mapped_column(
        Enum(DuplicateReviewStatus, name="duplicate_review_status"),
        nullable=False,
        default=DuplicateReviewStatus.PENDING,
        server_default=DuplicateReviewStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tender: Mapped[Tender] = relationship(back_populates="duplicate_candidates", foreign_keys=[tender_id])
    candidate_tender: Mapped[Tender] = relationship(foreign_keys=[candidate_tender_id])


class TenderDocument(Base):
    __tablename__ = "tender_documents"
    __table_args__ = (Index("ix_tender_documents_tender_id", "tender_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenders.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_name: Mapped[str] = mapped_column(String(500), nullable=False)
    document_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    tender: Mapped[Tender] = relationship(back_populates="documents")
