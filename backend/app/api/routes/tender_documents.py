"""Tender document processing APIs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config import Settings
from app.core.deps import get_db, get_settings, require_admin, require_authenticated_user
from app.core.enums import TenderDocumentDownloadStatus
from app.models.user import User
from app.schemas.tender_document import (
    TenderDocumentProcessRequest,
    TenderDocumentProcessingJobPublic,
    TenderDocumentPublic,
    TenderDocumentSummary,
)
from app.services.tender_document_job_service import TenderDocumentJobService
from app.services.tender_document_service import TenderDocumentService

router = APIRouter(tags=["tender-documents"])


def get_document_service(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TenderDocumentService:
    return TenderDocumentService(db, settings)


def get_job_service(db: Annotated[Session, Depends(get_db)]) -> TenderDocumentJobService:
    return TenderDocumentJobService(db)


@router.get("/tender-documents", response_model=list[TenderDocumentSummary])
def list_all_tender_documents(
    current_user: Annotated[User, Depends(require_authenticated_user)],
    service: Annotated[TenderDocumentService, Depends(get_document_service)],
    download_status: TenderDocumentDownloadStatus | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[TenderDocumentSummary]:
    _ = current_user
    return service.list_documents(download_status=download_status, limit=limit)


@router.get("/tenders/{tender_id}/documents", response_model=list[TenderDocumentSummary])
def list_tender_documents(
    tender_id: UUID,
    current_user: Annotated[User, Depends(require_authenticated_user)],
    service: Annotated[TenderDocumentService, Depends(get_document_service)],
) -> list[TenderDocumentSummary]:
    _ = current_user
    return service.list_documents_for_tender(tender_id)


@router.get("/tender-documents/{document_id}", response_model=TenderDocumentPublic)
def get_tender_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(require_authenticated_user)],
    service: Annotated[TenderDocumentService, Depends(get_document_service)],
) -> TenderDocumentPublic:
    _ = current_user
    return service.get_document_or_404(document_id)


@router.post("/tender-documents/{document_id}/process", response_model=TenderDocumentPublic)
async def process_tender_document(
    document_id: UUID,
    payload: TenderDocumentProcessRequest,
    current_admin: Annotated[User, Depends(require_admin)],
    service: Annotated[TenderDocumentService, Depends(get_document_service)],
) -> TenderDocumentPublic:
    _ = current_admin
    return await service.process_document(document_id, force=payload.force)


@router.post(
    "/tenders/{tender_id}/process-documents",
    response_model=TenderDocumentProcessingJobPublic,
    status_code=status.HTTP_202_ACCEPTED,
)
async def process_tender_documents(
    tender_id: UUID,
    payload: TenderDocumentProcessRequest,
    current_admin: Annotated[User, Depends(require_admin)],
    service: Annotated[TenderDocumentService, Depends(get_document_service)],
) -> TenderDocumentProcessingJobPublic:
    _ = current_admin
    job, _ = await service.process_tender_documents(tender_id, force=payload.force)
    return job


@router.get("/tender-document-jobs/{job_id}", response_model=TenderDocumentProcessingJobPublic)
def get_tender_document_job(
    job_id: UUID,
    current_user: Annotated[User, Depends(require_authenticated_user)],
    service: Annotated[TenderDocumentJobService, Depends(get_job_service)],
) -> TenderDocumentProcessingJobPublic:
    _ = current_user
    return service.get_job_or_404(job_id)
