"""Collection job persistence and query helpers."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import CollectionJobStatus, SourceHealthStatus
from app.models.tender_source import TenderCollectionEvent, TenderCollectionJob, TenderSource
from app.schemas.tender_source import CollectionJobPublic, CollectionJobSummary


class CollectionJobService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_jobs(
        self,
        *,
        source_id: UUID | None = None,
        limit: int = 50,
    ) -> list[CollectionJobSummary]:
        query = (
            select(TenderCollectionJob, TenderSource.name, TenderSource.code)
            .join(TenderSource, TenderSource.id == TenderCollectionJob.tender_source_id)
            .order_by(TenderCollectionJob.started_at.desc().nullslast(), TenderCollectionJob.created_at.desc())
            .limit(limit)
        )
        if source_id is not None:
            query = query.where(TenderCollectionJob.tender_source_id == source_id)

        rows = self.db.execute(query).all()
        summaries: list[CollectionJobSummary] = []
        for job, source_name, source_code in rows:
            summaries.append(
                CollectionJobSummary(
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
            )
        return summaries

    def get_job_or_404(self, job_id: UUID) -> CollectionJobPublic:
        job = self.db.scalar(
            select(TenderCollectionJob)
            .options(selectinload(TenderCollectionJob.events))
            .where(TenderCollectionJob.id == job_id)
        )
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection job not found.")

        source = self.db.get(TenderSource, job.tender_source_id)
        return CollectionJobPublic(
            id=job.id,
            tender_source_id=job.tender_source_id,
            source_name=source.name if source else None,
            source_code=source.code if source else None,
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
            events=list(job.events),
        )

    def create_job(self, source: TenderSource) -> TenderCollectionJob:
        job = TenderCollectionJob(
            tender_source_id=source.id,
            status=CollectionJobStatus.QUEUED,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def mark_running(self, job: TenderCollectionJob, source: TenderSource) -> None:
        now = datetime.now(UTC)
        job.status = CollectionJobStatus.RUNNING
        job.started_at = now
        source.last_collection_started_at = now
        self.db.commit()

    def finalize_job(
        self,
        job: TenderCollectionJob,
        source: TenderSource,
        *,
        status: CollectionJobStatus,
        error_message: str | None = None,
    ) -> None:
        now = datetime.now(UTC)
        job.status = status
        job.completed_at = now
        job.error_message = error_message
        if job.started_at:
            job.duration_seconds = round((now - job.started_at).total_seconds(), 2)
        source.last_collection_completed_at = now
        if status in {CollectionJobStatus.COMPLETED, CollectionJobStatus.PARTIAL}:
            source.last_success_at = now
            source.health_status = (
                SourceHealthStatus.DEGRADED if status == CollectionJobStatus.PARTIAL else SourceHealthStatus.HEALTHY
            )
            source.last_error = None
        elif status == CollectionJobStatus.FAILED:
            source.last_failure_at = now
            source.last_error = error_message
            source.health_status = SourceHealthStatus.FAILED
        self.db.commit()

    def log_event(
        self,
        *,
        job: TenderCollectionJob,
        source_id: UUID,
        level,
        message: str,
        error_type=None,
        context: dict | None = None,
    ) -> TenderCollectionEvent:
        event = TenderCollectionEvent(
            job_id=job.id,
            tender_source_id=source_id,
            level=level,
            message=message,
            error_type=error_type,
            context=context,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
