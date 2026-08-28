"""Discover and upsert tender document references."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import TenderDocumentDownloadStatus
from app.document_processing.classification import classify_document
from app.document_processing.identity import resolve_source_document_id
from app.models.tender import TenderDocument


def upsert_discovered_document(
    db: Session,
    *,
    tender_id: UUID,
    document_name: str,
    document_url: str | None,
    source_document_id: str | None,
    document_type: str | None = None,
) -> TenderDocument:
    resolved_id = resolve_source_document_id(
        document_id=source_document_id,
        document_name=document_name,
        document_url=document_url,
        tender_id=tender_id,
    )
    existing = db.scalar(
        select(TenderDocument).where(
            TenderDocument.tender_id == tender_id,
            TenderDocument.source_document_id == resolved_id,
        )
    )
    now = datetime.now(UTC)
    classification = classify_document(
        document_name=document_name,
        document_url=document_url,
        source_document_type=document_type,
    )
    if existing:
        existing.document_name = document_name
        existing.document_url = document_url or existing.document_url
        existing.document_type = document_type or existing.document_type
        existing.source_reference = resolved_id
        existing.classification = classification
        return existing

    document = TenderDocument(
        tender_id=tender_id,
        source_document_id=resolved_id,
        source_reference=resolved_id,
        document_name=document_name,
        document_url=document_url,
        document_type=document_type,
        classification=classification,
        download_status=TenderDocumentDownloadStatus.DISCOVERED,
        first_seen_at=now,
    )
    db.add(document)
    return document
