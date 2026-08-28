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
from app.core.enums import TenderStatus


class Tender(Base):
    __tablename__ = "tenders"
    __table_args__ = (
        UniqueConstraint("tender_source_id", "source_tender_id", name="uq_tenders_source_tender_id"),
        Index("ix_tenders_source_id", "tender_source_id"),
        Index("ix_tenders_status", "status"),
        Index("ix_tenders_reference_number", "reference_number"),
        Index("ix_tenders_submission_end", "submission_end"),
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
