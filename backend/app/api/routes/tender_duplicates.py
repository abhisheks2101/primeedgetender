"""Duplicate candidate review APIs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin
from app.core.enums import DuplicateReviewStatus
from app.models.user import User
from app.schemas.tender import TenderDuplicateCandidatePublic, TenderDuplicateReviewUpdate
from app.services.deduplication_service import DeduplicationService

router = APIRouter(prefix="/tender-duplicates", tags=["tender-duplicates"])


def get_deduplication_service(db: Annotated[Session, Depends(get_db)]) -> DeduplicationService:
    return DeduplicationService(db)


@router.get("", response_model=list[TenderDuplicateCandidatePublic])
def list_duplicate_candidates(
    current_admin: Annotated[User, Depends(require_admin)],
    service: Annotated[DeduplicationService, Depends(get_deduplication_service)],
    review_status: DuplicateReviewStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[TenderDuplicateCandidatePublic]:
    """List duplicate candidates for administrative review."""
    _ = current_admin
    return service.list_candidates(review_status=review_status, limit=limit)


@router.get("/{candidate_id}", response_model=TenderDuplicateCandidatePublic)
def get_duplicate_candidate(
    candidate_id: UUID,
    current_admin: Annotated[User, Depends(require_admin)],
    service: Annotated[DeduplicationService, Depends(get_deduplication_service)],
) -> TenderDuplicateCandidatePublic:
    """Return one duplicate candidate with both tender summaries."""
    _ = current_admin
    try:
        return service.get_candidate_or_404(candidate_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{candidate_id}", response_model=TenderDuplicateCandidatePublic)
def review_duplicate_candidate(
    candidate_id: UUID,
    payload: TenderDuplicateReviewUpdate,
    current_admin: Annotated[User, Depends(require_admin)],
    service: Annotated[DeduplicationService, Depends(get_deduplication_service)],
) -> TenderDuplicateCandidatePublic:
    """Mark a duplicate candidate as confirmed, rejected, or ignored."""
    _ = current_admin
    if payload.review_status == DuplicateReviewStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use CONFIRMED_DUPLICATE, NOT_DUPLICATE, or IGNORED.",
        )
    try:
        return service.review_candidate(candidate_id, review_status=payload.review_status)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
