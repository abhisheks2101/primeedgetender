"""Tender persistence with normalization and deduplication."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base import NormalizedTenderDraft, RawDocumentRef
from app.core.enums import NormalizationStatus
from app.models.tender import Tender, TenderChangeHistory
from app.document_processing.discovery import upsert_discovered_document
from app.normalization.pipeline import normalize_draft
from app.services.deduplication_service import DeduplicationService


class TenderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.deduplication_service = DeduplicationService(db)

    def get_by_source_tender_id(self, source_id: UUID, source_tender_id: str) -> Tender | None:
        return self.db.scalar(
            select(Tender).where(
                Tender.tender_source_id == source_id,
                Tender.source_tender_id == source_tender_id,
            )
        )

    def get_by_id(self, tender_id: UUID) -> Tender | None:
        return self.db.get(Tender, tender_id)

    def list_tenders(self, *, limit: int = 50) -> list[Tender]:
        return list(self.db.scalars(select(Tender).order_by(Tender.updated_at.desc()).limit(limit)).all())

    @staticmethod
    def payload_hash(payload: dict) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()

    def upsert_from_draft(
        self,
        *,
        source_id: UUID,
        source_code: str,
        draft: NormalizedTenderDraft,
        payload: dict,
        documents: list[RawDocumentRef],
    ) -> tuple[Tender, str]:
        normalized = normalize_draft(draft, source_code=source_code)
        if normalized.normalization_status == NormalizationStatus.FAILED:
            raise ValueError(
                "Normalized tender failed validation: "
                + ", ".join(normalized.validation_warnings or ["unknown error"])
            )

        payload_hash = self.payload_hash(payload)
        existing = self.get_by_source_tender_id(source_id, normalized.source_tender_id)
        now = datetime.now(UTC)

        if existing and existing.payload_hash == payload_hash and existing.normalization_version == normalized.normalization_version:
            existing.last_seen_at = now
            return existing, "skipped"

        if existing:
            tender = existing
            action = "updated"
            self._record_changes(tender, normalized)
        else:
            tender = Tender(tender_source_id=source_id, source_tender_id=normalized.source_tender_id)
            tender.first_seen_at = now
            self.db.add(tender)
            action = "created"

        tender.reference_number = normalized.reference_number
        tender.title = normalized.title
        tender.work_description = normalized.work_description
        tender.organization = normalized.organization
        tender.department = normalized.department
        tender.tender_type = normalized.tender_type
        tender.tender_category = normalized.tender_category
        tender.location = normalized.location
        tender.district = normalized.district
        tender.state = normalized.state
        tender.state_code = normalized.state_code
        tender.original_location_text = normalized.original_location_text
        tender.title_normalized = normalized.title_normalized
        tender.description_normalized = normalized.description_normalized
        tender.organization_normalized = normalized.organization_normalized
        tender.estimated_value = normalized.estimated_value
        tender.emd_amount = normalized.emd_amount
        tender.tender_fee = normalized.tender_fee
        tender.publication_date = normalized.publication_date
        tender.document_sale_start = normalized.document_sale_start
        tender.document_sale_end = normalized.document_sale_end
        tender.submission_start = normalized.submission_start
        tender.submission_end = normalized.submission_end
        tender.opening_date = normalized.opening_date
        tender.status = normalized.status
        tender.source_status = normalized.source_status
        tender.source_url = normalized.source_url
        tender.raw_payload = payload
        tender.payload_hash = payload_hash
        tender.source_last_updated = normalized.source_last_updated
        tender.normalization_version = normalized.normalization_version
        tender.normalization_status = normalized.normalization_status
        tender.validation_warnings = normalized.validation_warnings or None
        tender.last_seen_at = now
        tender.normalized_at = now

        self.db.flush()
        self._replace_documents(tender, documents)
        self.deduplication_service.detect_candidates(tender)
        return tender, action

    def reprocess_tender(self, tender: Tender, *, source_code: str) -> Tender:
        if not tender.raw_payload:
            tender.normalization_status = NormalizationStatus.FAILED
            return tender
        payload = tender.raw_payload
        summary = payload.get("summary", payload)
        detail = payload.get("detail", payload)
        draft = NormalizedTenderDraft(
            source_code=source_code,
            source_tender_id=tender.source_tender_id,
            reference_number=detail.get("reference_number") or summary.get("reference_number") or tender.reference_number,
            title=detail.get("title") or summary.get("title") or tender.title,
            work_description=detail.get("work_description") or tender.work_description,
            organization=detail.get("organization") or tender.organization,
            department=detail.get("department") or tender.department,
            tender_type=detail.get("tender_type") or tender.tender_type,
            tender_category=detail.get("tender_category") or tender.tender_category,
            location=detail.get("location") or tender.location,
            district=detail.get("district") or tender.district,
            state=detail.get("state") or tender.state,
            estimated_value=detail.get("estimated_value") or tender.estimated_value,
            emd_amount=detail.get("emd_amount") or tender.emd_amount,
            tender_fee=detail.get("tender_fee") or tender.tender_fee,
            publication_date=detail.get("publication_date") or tender.publication_date,
            document_sale_start=detail.get("document_sale_start") or tender.document_sale_start,
            document_sale_end=detail.get("document_sale_end") or tender.document_sale_end,
            submission_start=detail.get("submission_start") or tender.submission_start,
            submission_end=detail.get("submission_end") or tender.submission_end,
            opening_date=detail.get("opening_date") or tender.opening_date,
            status=tender.status,
            source_status=detail.get("source_status") or tender.source_status,
            source_url=detail.get("detail_url") or summary.get("detail_url") or tender.source_url,
            source_last_updated=tender.source_last_updated,
            raw_payload=tender.raw_payload,
            documents=[
                RawDocumentRef(
                    document_id=doc.document_type or doc.document_name,
                    title=doc.document_name,
                    url=doc.document_url,
                )
                for doc in tender.documents
            ],
        )
        updated, _ = self.upsert_from_draft(
            source_id=tender.tender_source_id,
            source_code=source_code,
            draft=draft,
            payload=tender.raw_payload,
            documents=draft.documents,
        )
        return updated

    def reprocess_all_for_source(self, source_id: UUID, *, source_code: str, limit: int = 500) -> int:
        tenders = list(
            self.db.scalars(
                select(Tender).where(Tender.tender_source_id == source_id).order_by(Tender.updated_at.desc()).limit(limit)
            ).all()
        )
        processed = 0
        for tender in tenders:
            self.reprocess_tender(tender, source_code=source_code)
            processed += 1
        return processed

    def _record_changes(self, tender: Tender, normalized) -> None:
        tracked = {
            "status": (tender.status.value if tender.status else None, normalized.status.value),
            "estimated_value": (str(tender.estimated_value) if tender.estimated_value is not None else None, str(normalized.estimated_value) if normalized.estimated_value is not None else None),
            "submission_end": (tender.submission_end.isoformat() if tender.submission_end else None, normalized.submission_end.isoformat() if normalized.submission_end else None),
        }
        for field_name, (old_value, new_value) in tracked.items():
            if old_value != new_value:
                self.db.add(
                    TenderChangeHistory(
                        tender_id=tender.id,
                        field_name=field_name,
                        old_value=old_value,
                        new_value=new_value,
                    )
                )

    def _replace_documents(self, tender: Tender, documents: list[RawDocumentRef]) -> None:
        if not documents:
            return
        for doc in documents:
            upsert_discovered_document(
                self.db,
                tender_id=tender.id,
                document_name=doc.title or doc.document_id,
                document_url=doc.url,
                source_document_id=doc.document_id,
                document_type=doc.document_id if doc.document_id else None,
            )
