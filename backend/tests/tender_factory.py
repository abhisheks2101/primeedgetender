"""Shared tender test data helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.collectors.base import NormalizedTenderDraft, RawDocumentRef
from app.core.enums import CollectionMethod, TenderSourceType, TenderStatus
from app.schemas.tender_source import SourceConfiguration, TenderSourceCreate
from app.services.tender_service import TenderService
from app.services.tender_source_service import TenderSourceService


def create_source(db: Session, *, code: str, state: str | None = None) -> UUID:
    service = TenderSourceService(db)
    source = service.create_source(
        TenderSourceCreate(
            name=f"Test {code}",
            code=code,
            state=state,
            authority="Test Authority",
            portal_url="https://example.test/portal",
            source_type=TenderSourceType.GOVERNMENT_PORTAL,
            collection_method=CollectionMethod.HTML,
            configuration=SourceConfiguration(source_url="https://example.test/source"),
        )
    )
    db.commit()
    return source.id


def upsert_test_tender(
    db: Session,
    *,
    source_id: UUID,
    source_code: str,
    source_tender_id: str,
    title: str,
    reference_number: str | None = None,
    organization: str | None = None,
    location: str | None = None,
    state: str | None = None,
    estimated_value: Decimal | str | None = None,
    submission_end: datetime | None = None,
    status: TenderStatus = TenderStatus.OPEN,
    source_status: str | None = "Active",
) -> tuple:
    service = TenderService(db)
    detail_url = f"https://example.test/tenders/{source_tender_id}"
    payload = {
        "summary": {
            "title": title,
            "reference_number": reference_number,
            "detail_url": detail_url,
        },
        "detail": {
            "title": title,
            "reference_number": reference_number,
            "organization": organization,
            "location": location,
            "state": state,
            "estimated_value": str(estimated_value) if estimated_value is not None else None,
            "submission_end": submission_end.isoformat() if submission_end else None,
            "detail_url": detail_url,
        },
    }
    draft = NormalizedTenderDraft(
        source_code=source_code,
        source_tender_id=source_tender_id,
        reference_number=reference_number,
        title=title,
        organization=organization,
        location=location,
        state=state,
        estimated_value=Decimal(str(estimated_value)) if estimated_value is not None else None,
        submission_end=submission_end,
        status=status,
        source_status=source_status,
        source_url=detail_url,
        raw_payload=payload,
    )
    tender, action = service.upsert_from_draft(
        source_id=source_id,
        source_code=source_code,
        draft=draft,
        payload=payload,
        documents=[
            RawDocumentRef(
                document_id=f"{source_tender_id}-doc",
                title="Notice",
                url=f"{detail_url}/notice.pdf",
            )
        ],
    )
    db.commit()
    return tender, action


def future_date(days: int = 30) -> datetime:
    return datetime.now(UTC) + timedelta(days=days)
