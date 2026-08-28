"""Tender document processing job helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import TenderDocumentProcessingJobStatus
from app.models.tender import TenderDocumentProcessingEvent, TenderDocumentProcessingJob


class TenderDocumentJobService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(self, tender_id: UUID) -> TenderDocumentProcessingJob:
        job = TenderDocumentProcessingJob(tender_id=tender_id, status=TenderDocumentProcessingJobStatus.QUEUED)
        self.db.add(job)
        self.db.flush()
        return job

    def mark_running(self, job: TenderDocumentProcessingJob) -> None:
        job.status = TenderDocumentProcessingJobStatus.RUNNING
        job.started_at = datetime.now(UTC)

    def finalize_job(self, job: TenderDocumentProcessingJob) -> None:
        now = datetime.now(UTC)
        job.completed_at = now
        if job.started_at:
            job.duration_seconds = round((now - job.started_at).total_seconds(), 2)
        if job.failed and (job.downloaded or job.extracted or job.skipped):
            job.status = TenderDocumentProcessingJobStatus.PARTIAL
        elif job.failed and not (job.downloaded or job.extracted or job.skipped):
            job.status = TenderDocumentProcessingJobStatus.FAILED
        else:
            job.status = TenderDocumentProcessingJobStatus.COMPLETED
        self.db.commit()

    def get_job_or_404(self, job_id: UUID) -> TenderDocumentProcessingJob:
        job = self.db.scalar(
            select(TenderDocumentProcessingJob)
            .options(selectinload(TenderDocumentProcessingJob.events))
            .where(TenderDocumentProcessingJob.id == job_id)
        )
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document processing job not found.")
        return job
