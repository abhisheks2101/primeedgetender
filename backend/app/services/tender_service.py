"""Persistence helpers for normalized tenders."""

from __future__ import annotations

import hashlib
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.collectors.base import NormalizedTenderDraft, RawDocumentRef
from app.models.tender import Tender, TenderDocument


class TenderService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_source_tender_id(self, source_id: UUID, source_tender_id: str) -> Tender | None:
        return self.db.scalar(
            select(Tender).where(
                Tender.tender_source_id == source_id,
                Tender.source_tender_id == source_tender_id,
            )
        )

    @staticmethod
    def payload_hash(payload: dict) -> str:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()

    def upsert_from_draft(
        self,
        *,
        source_id: UUID,
        draft: NormalizedTenderDraft,
        payload: dict,
        documents: list[RawDocumentRef],
    ) -> tuple[Tender, str]:
        payload_hash = self.payload_hash(payload)
        existing = self.get_by_source_tender_id(source_id, draft.source_tender_id)

        if existing and existing.payload_hash == payload_hash:
            return existing, "skipped"

        if existing:
            tender = existing
            action = "updated"
        else:
            tender = Tender(tender_source_id=source_id, source_tender_id=draft.source_tender_id)
            self.db.add(tender)
            action = "created"

        tender.reference_number = draft.reference_number
        tender.title = draft.title
        tender.work_description = draft.work_description
        tender.organization = draft.organization
        tender.department = draft.department
        tender.tender_type = draft.tender_type
        tender.tender_category = draft.tender_category
        tender.location = draft.location
        tender.district = draft.district
        tender.state = draft.state
        tender.estimated_value = draft.estimated_value
        tender.emd_amount = draft.emd_amount
        tender.tender_fee = draft.tender_fee
        tender.publication_date = draft.publication_date
        tender.document_sale_start = draft.document_sale_start
        tender.document_sale_end = draft.document_sale_end
        tender.submission_start = draft.submission_start
        tender.submission_end = draft.submission_end
        tender.opening_date = draft.opening_date
        tender.status = draft.status
        tender.source_status = draft.source_status
        tender.source_url = draft.source_url
        tender.raw_payload = payload
        tender.payload_hash = payload_hash
        tender.source_last_updated = draft.source_last_updated

        self.db.flush()
        self._replace_documents(tender, documents)
        return tender, action

    def _replace_documents(self, tender: Tender, documents: list[RawDocumentRef]) -> None:
        tender.documents.clear()
        for doc in documents:
            tender.documents.append(
                TenderDocument(
                    document_name=doc.title or doc.document_id,
                    document_url=doc.url,
                    document_type=doc.document_id if doc.document_id else None,
                    source_reference=doc.document_id,
                )
            )
