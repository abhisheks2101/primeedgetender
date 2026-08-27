"""Tender source management routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_tender_source_read, require_tender_source_write
from app.models.user import User
from app.schemas.tender_source import (
    CollectionJobSummary,
    MessageResponse,
    TenderSourceCreate,
    TenderSourcePublic,
    TenderSourceStatusUpdate,
    TenderSourceSummary,
    TenderSourceUpdate,
)
from app.services.collection_job_service import CollectionJobService
from app.services.tender_source_service import TenderSourceService

router = APIRouter(prefix="/tender-sources", tags=["tender-sources"])


def get_source_service(db: Annotated[Session, Depends(get_db)]) -> TenderSourceService:
    return TenderSourceService(db)


def get_job_service(db: Annotated[Session, Depends(get_db)]) -> CollectionJobService:
    return CollectionJobService(db)


@router.get("", response_model=list[TenderSourceSummary])
def list_tender_sources(
    _: Annotated[User, Depends(require_tender_source_read)],
    service: Annotated[TenderSourceService, Depends(get_source_service)],
    active_only: bool | None = Query(default=None),
    state: str | None = Query(default=None),
) -> list[TenderSourceSummary]:
    return [TenderSourceSummary.model_validate(item) for item in service.list_sources(active_only=active_only, state=state)]


@router.post("", response_model=TenderSourcePublic, status_code=status.HTTP_201_CREATED)
def create_tender_source(
    payload: TenderSourceCreate,
    _: Annotated[User, Depends(require_tender_source_write)],
    service: Annotated[TenderSourceService, Depends(get_source_service)],
) -> TenderSourcePublic:
    return TenderSourcePublic.model_validate(service.create_source(payload))


@router.get("/{source_id}", response_model=TenderSourcePublic)
def get_tender_source(
    source_id: UUID,
    _: Annotated[User, Depends(require_tender_source_read)],
    service: Annotated[TenderSourceService, Depends(get_source_service)],
) -> TenderSourcePublic:
    return TenderSourcePublic.model_validate(service.get_source_or_404(source_id))


@router.patch("/{source_id}", response_model=TenderSourcePublic)
def update_tender_source(
    source_id: UUID,
    payload: TenderSourceUpdate,
    _: Annotated[User, Depends(require_tender_source_write)],
    service: Annotated[TenderSourceService, Depends(get_source_service)],
) -> TenderSourcePublic:
    return TenderSourcePublic.model_validate(service.update_source(source_id, payload))


@router.patch("/{source_id}/status", response_model=TenderSourcePublic)
def update_tender_source_status(
    source_id: UUID,
    payload: TenderSourceStatusUpdate,
    _: Annotated[User, Depends(require_tender_source_write)],
    service: Annotated[TenderSourceService, Depends(get_source_service)],
) -> TenderSourcePublic:
    return TenderSourcePublic.model_validate(service.update_status(source_id, payload))


@router.get("/{source_id}/jobs", response_model=list[CollectionJobSummary])
def list_source_collection_jobs(
    source_id: UUID,
    _: Annotated[User, Depends(require_tender_source_read)],
    source_service: Annotated[TenderSourceService, Depends(get_source_service)],
    job_service: Annotated[CollectionJobService, Depends(get_job_service)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[CollectionJobSummary]:
    source_service.get_source_or_404(source_id)
    return job_service.list_jobs(source_id=source_id, limit=limit)
