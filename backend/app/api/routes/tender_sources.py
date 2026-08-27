"""Tender source management routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.collectors.registry import get_collector_for_source
from app.core.deps import get_db, require_tender_source_read, require_tender_source_write
from app.models.user import User
from app.schemas.tender_source import (
    CollectionJobSummary,
    TenderSourceCreate,
    TenderSourcePublic,
    TenderSourceStatusUpdate,
    TenderSourceSummary,
    TenderSourceUpdate,
)
from app.services.collection_job_service import CollectionJobService
from app.services.collection_runner import CollectionRunner
from app.services.tender_source_service import TenderSourceService

router = APIRouter(prefix="/tender-sources", tags=["tender-sources"])

COLLECTABLE_SOURCE_CODES = {"UP_TENDER", "MOCK"}


def get_source_service(db: Annotated[Session, Depends(get_db)]) -> TenderSourceService:
    return TenderSourceService(db)


def get_job_service(db: Annotated[Session, Depends(get_db)]) -> CollectionJobService:
    return CollectionJobService(db)


def _job_to_summary(job, source_name: str | None = None, source_code: str | None = None) -> CollectionJobSummary:
    return CollectionJobSummary(
        id=job.id,
        tender_source_id=job.tender_source_id,
        source_name=source_name,
        source_code=source_code,
        status=job.status,
        started_at=job.started_at,
        completed_at=job.completed_at,
        records_discovered=job.records_discovered,
        records_processed=job.records_processed,
        records_created=job.records_created,
        records_updated=job.records_updated,
        records_skipped=job.records_skipped,
        records_failed=job.records_failed,
        duration_seconds=job.duration_seconds,
        error_message=job.error_message,
        created_at=job.created_at,
    )


async def _execute_collection(source_id: UUID, job_id: UUID, session_factory) -> None:
    with session_factory() as db:
        source = TenderSourceService(db).get_source_or_404(source_id)
        collector = get_collector_for_source(source)
        if collector is None:
            return
        runner = CollectionRunner(db)
        await runner.run_with_collector(source_id, collector, job_id=job_id)


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


@router.post("/{source_id}/collect", response_model=CollectionJobSummary, status_code=status.HTTP_202_ACCEPTED)
async def trigger_tender_collection(
    source_id: UUID,
    request: Request,
    _: Annotated[User, Depends(require_tender_source_write)],
    source_service: Annotated[TenderSourceService, Depends(get_source_service)],
    job_service: Annotated[CollectionJobService, Depends(get_job_service)],
    background_tasks: BackgroundTasks,
) -> CollectionJobSummary:
    source = source_service.get_source_or_404(source_id)
    if not source.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tender source is inactive.")

    collector = get_collector_for_source(source)
    if collector is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No collector registered for source code {source.code}.",
        )

    if source.code not in COLLECTABLE_SOURCE_CODES and not source.code.startswith("TEST_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Manual collection is not enabled for source code {source.code}.",
        )

    job = job_service.create_job(source)
    session_factory = request.app.state.db_session_factory
    background_tasks.add_task(_execute_collection, source.id, job.id, session_factory)
    return _job_to_summary(job, source.name, source.code)


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
