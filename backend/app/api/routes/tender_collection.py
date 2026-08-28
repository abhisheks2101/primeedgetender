"""Tender collection job history routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_tender_source_read
from app.models.user import User
from app.schemas.tender_source import CollectionJobPublic, CollectionJobSummary
from app.services.collection_job_service import CollectionJobService

router = APIRouter(prefix="/tender-collection", tags=["tender-collection"])


def get_job_service(db: Annotated[Session, Depends(get_db)]) -> CollectionJobService:
    return CollectionJobService(db)


@router.get("/jobs", response_model=list[CollectionJobSummary])
def list_collection_jobs(
    _: Annotated[User, Depends(require_tender_source_read)],
    service: Annotated[CollectionJobService, Depends(get_job_service)],
    limit: int = Query(default=50, ge=1, le=100),
) -> list[CollectionJobSummary]:
    return service.list_jobs(limit=limit)


@router.get("/jobs/{job_id}", response_model=CollectionJobPublic)
def get_collection_job(
    job_id: UUID,
    _: Annotated[User, Depends(require_tender_source_read)],
    service: Annotated[CollectionJobService, Depends(get_job_service)],
) -> CollectionJobPublic:
    return service.get_job_or_404(job_id)
