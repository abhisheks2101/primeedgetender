"""Tender document discovery and processing."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import Settings
from app.core.enums import TenderDocumentDownloadStatus
from app.document_processing.pipeline import DocumentProcessingPipeline
from app.models.tender import Tender, TenderDocument, TenderDocumentProcessingJob
from app.services.tender_document_job_service import TenderDocumentJobService
from app.services.tender_service import TenderService


class TenderDocumentService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.tender_service = TenderService(db)
        self.job_service = TenderDocumentJobService(db)
        self.pipeline = DocumentProcessingPipeline(db, settings)

    def list_documents(
        self,
        *,
        tender_id: UUID | None = None,
        download_status: TenderDocumentDownloadStatus | None = None,
        limit: int = 100,
    ) -> list[TenderDocument]:
        query = select(TenderDocument).options(selectinload(TenderDocument.pages)).order_by(TenderDocument.updated_at.desc())
        if tender_id is not None:
            query = query.where(TenderDocument.tender_id == tender_id)
        if download_status is not None:
            query = query.where(TenderDocument.download_status == download_status)
        return list(self.db.scalars(query.limit(limit)).all())

    def get_document_or_404(self, document_id: UUID) -> TenderDocument:
        document = self.db.scalar(
            select(TenderDocument)
            .options(selectinload(TenderDocument.pages), selectinload(TenderDocument.tender))
            .where(TenderDocument.id == document_id)
        )
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender document not found.")
        return document

    def list_documents_for_tender(self, tender_id: UUID) -> list[TenderDocument]:
        self.tender_service.get_by_id(tender_id) or self._raise_tender_missing()
        return self.list_documents(tender_id=tender_id, limit=self.settings.max_documents_per_job)

    async def process_document(self, document_id: UUID, *, force: bool = False) -> TenderDocument:
        document = self.get_document_or_404(document_id)
        job = self.job_service.create_job(document.tender_id)
        self.job_service.mark_running(job)
        job.discovered = 1
        await self.pipeline.process_document(document, job=job, force=force)
        self.job_service.finalize_job(job)
        self.db.refresh(document)
        return document

    async def process_tender_documents(self, tender_id: UUID, *, force: bool = False) -> tuple[TenderDocumentProcessingJob, list[TenderDocument]]:
        tender = self.tender_service.get_by_id(tender_id)
        if tender is None:
            self._raise_tender_missing()

        documents = self.list_documents_for_tender(tender_id)
        if not documents:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No documents discovered for this tender.")

        job = self.job_service.create_job(tender_id)
        self.job_service.mark_running(job)
        job.discovered = len(documents[: self.settings.max_documents_per_job])

        processed: list[TenderDocument] = []
        for document in documents[: self.settings.max_documents_per_job]:
            await self.pipeline.process_document(document, job=job, force=force)
            processed.append(document)

        self.job_service.finalize_job(job)
        return job, processed

    def _raise_tender_missing(self) -> None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tender not found.")
