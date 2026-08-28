"""Normalized tender read APIs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_authenticated_user
from app.models.user import User
from app.schemas.tender import TenderPublic, TenderSummary
from app.services.tender_service import TenderService

router = APIRouter(prefix="/tenders", tags=["tenders"])


def get_tender_service(db: Annotated[Session, Depends(get_db)]) -> TenderService:
    return TenderService(db)


@router.get("", response_model=list[TenderSummary])
def list_tenders(
    current_user: Annotated[User, Depends(require_authenticated_user)],
    service: Annotated[TenderService, Depends(get_tender_service)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[TenderSummary]:
    """List normalized tenders for administration and testing."""
    _ = current_user
    return service.list_tenders(limit=limit)


@router.get("/{tender_id}", response_model=TenderPublic)
def get_tender(
    tender_id: UUID,
    current_user: Annotated[User, Depends(require_authenticated_user)],
    service: Annotated[TenderService, Depends(get_tender_service)],
) -> TenderPublic:
    """Return one normalized tender with documents and normalization metadata."""
    _ = current_user
    tender = service.get_by_id(tender_id)
    if tender is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found.")
    return tender
