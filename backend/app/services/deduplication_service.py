"""Deduplication and duplicate candidate management."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.enums import DuplicateMatchType, DuplicateReviewStatus
from app.models.tender import Tender, TenderDuplicateCandidate
from app.models.tender_source import TenderSource
from app.normalization.config import DEFAULT_THRESHOLDS, DeduplicationThresholds
from app.normalization.deduplication import compare_tenders


class DeduplicationService:
    def __init__(self, db: Session, *, thresholds: DeduplicationThresholds = DEFAULT_THRESHOLDS) -> None:
        self.db = db
        self.thresholds = thresholds

    def detect_candidates(self, tender: Tender) -> list[TenderDuplicateCandidate]:
        source = self.db.get(TenderSource, tender.tender_source_id)
        source_code = source.code if source else ""
        candidates = self._find_candidate_tenders(tender)
        created: list[TenderDuplicateCandidate] = []
        for candidate in candidates:
            result = compare_tenders(
                tender,
                candidate,
                left_source_code=source_code,
                right_source_code=self._source_code(candidate),
                thresholds=self.thresholds,
            )
            if result.match_type == DuplicateMatchType.NOT_DUPLICATE:
                continue
            existing = self.db.scalar(
                select(TenderDuplicateCandidate).where(
                    TenderDuplicateCandidate.tender_id == tender.id,
                    TenderDuplicateCandidate.candidate_tender_id == candidate.id,
                )
            )
            if existing:
                existing.match_type = result.match_type
                existing.confidence = round(result.confidence, 4)
                existing.matched_fields = result.matched_fields
                created.append(existing)
                continue
            record = TenderDuplicateCandidate(
                tender_id=tender.id,
                candidate_tender_id=candidate.id,
                match_type=result.match_type,
                confidence=round(result.confidence, 4),
                matched_fields=result.matched_fields,
                review_status=DuplicateReviewStatus.PENDING,
            )
            self.db.add(record)
            created.append(record)
        return created

    def _find_candidate_tenders(self, tender: Tender) -> list[Tender]:
        query = select(Tender).where(Tender.id != tender.id)
        filters = []
        if tender.reference_number:
            filters.append(Tender.reference_number == tender.reference_number)
        if tender.state_code:
            filters.append(Tender.state_code == tender.state_code)
        if tender.organization_normalized:
            filters.append(Tender.organization_normalized == tender.organization_normalized)
        if filters:
            query = query.where(or_(*filters))
        else:
            return []
        return list(self.db.scalars(query.limit(25)).all())

    def _source_code(self, tender: Tender) -> str:
        source = self.db.get(TenderSource, tender.tender_source_id)
        return source.code if source else ""

    def list_candidates(self, *, review_status: DuplicateReviewStatus | None = None, limit: int = 50) -> list[TenderDuplicateCandidate]:
        query = (
            select(TenderDuplicateCandidate)
            .options(
                joinedload(TenderDuplicateCandidate.tender),
                joinedload(TenderDuplicateCandidate.candidate_tender),
            )
            .order_by(TenderDuplicateCandidate.created_at.desc())
            .limit(limit)
        )
        if review_status is not None:
            query = query.where(TenderDuplicateCandidate.review_status == review_status)
        return list(self.db.scalars(query).unique().all())

    def get_candidate_or_404(self, candidate_id: UUID) -> TenderDuplicateCandidate:
        candidate = self.db.scalar(
            select(TenderDuplicateCandidate)
            .options(
                joinedload(TenderDuplicateCandidate.tender),
                joinedload(TenderDuplicateCandidate.candidate_tender),
            )
            .where(TenderDuplicateCandidate.id == candidate_id)
        )
        if candidate is None:
            raise ValueError("Duplicate candidate not found.")
        return candidate

    def review_candidate(
        self,
        candidate_id: UUID,
        *,
        review_status: DuplicateReviewStatus,
    ) -> TenderDuplicateCandidate:
        candidate = self.get_candidate_or_404(candidate_id)
        candidate.review_status = review_status
        candidate.reviewed_at = datetime.now(UTC)
        self.db.commit()
        return candidate
