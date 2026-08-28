"""Integration tests for tender document processing pipeline."""

from unittest.mock import AsyncMock

import pytest

from app.config import Settings
from app.core.enums import (
    TenderDocumentDownloadStatus,
    TenderDocumentExtractionStatus,
    TenderDocumentProcessingStatus,
)
from app.document_processing.downloader import DownloadResult
from app.document_processing.pipeline import DocumentProcessingPipeline
from app.document_processing.discovery import upsert_discovered_document
from app.services.tender_document_service import TenderDocumentService
from tests.document_fixtures import make_pdf_bytes
from tests.helpers import login
from tests.tender_factory import create_source, upsert_test_tender


@pytest.fixture
def document_settings(tmp_path):
    return Settings(
        app_env="test",
        auth_secret="test-secret",
        document_storage_path=str(tmp_path / "tenders"),
        document_allowed_domains="example.test",
        ocr_enabled=False,
    )


@pytest.fixture
def up_source(db):
    return create_source(db, code="UP_TENDER", state="Uttar Pradesh")


@pytest.mark.asyncio
async def test_document_processing_pipeline_end_to_end(db, up_source, document_settings):
    tender, _ = upsert_test_tender(
        db,
        source_id=up_source,
        source_code="UP_TENDER",
        source_tender_id="DOC-001",
        title="Document Processing Tender",
        reference_number="DOC-REF-1",
    )
    document = upsert_discovered_document(
        db,
        tender_id=tender.id,
        document_name="NIT Document",
        document_url="https://example.test/nit.pdf",
        source_document_id="nit-1",
        document_type="NIT",
    )
    db.commit()

    pipeline = DocumentProcessingPipeline(db, document_settings)
    pdf_bytes = make_pdf_bytes(["Minimum turnover requirement on page 1", "Eligibility criteria on page 2"])
    pipeline.downloader.download = AsyncMock(
        return_value=DownloadResult(True, content=pdf_bytes, content_type="application/pdf", status_code=200)
    )

    processed = await pipeline.process_document(document)
    db.commit()
    db.refresh(processed)

    assert processed.download_status == TenderDocumentDownloadStatus.DOWNLOADED
    assert processed.processing_status == TenderDocumentProcessingStatus.VALIDATED
    assert processed.extraction_status == TenderDocumentExtractionStatus.TEXT_EXTRACTED
    assert processed.page_count == 2
    assert processed.checksum
    assert len(processed.pages) == 2
    assert processed.pages[1].page_number == 2


@pytest.mark.asyncio
async def test_document_processing_is_idempotent(db, up_source, document_settings):
    tender, _ = upsert_test_tender(
        db,
        source_id=up_source,
        source_code="UP_TENDER",
        source_tender_id="DOC-002",
        title="Idempotent Tender",
        reference_number="DOC-REF-2",
    )
    document = upsert_discovered_document(
        db,
        tender_id=tender.id,
        document_name="BOQ",
        document_url="https://example.test/boq.pdf",
        source_document_id="boq-1",
    )
    db.commit()

    service = TenderDocumentService(db, document_settings)
    service.pipeline.downloader.download = AsyncMock(
        return_value=DownloadResult(True, content=make_pdf_bytes(["BOQ line item"]), content_type="application/pdf")
    )

    first = await service.process_document(document.id)
    download_mock = service.pipeline.downloader.download
    second = await service.process_document(document.id)
    assert download_mock.await_count == 1
    assert second.download_status == TenderDocumentDownloadStatus.DOWNLOADED


@pytest.fixture
def admin_client(api_client, created_admin):
    login(api_client, created_admin.email, "AdminPass123")
    return api_client


def test_process_documents_api(db, admin_client, up_source, document_settings, monkeypatch):
    tender, _ = upsert_test_tender(
        db,
        source_id=up_source,
        source_code="UP_TENDER",
        source_tender_id="DOC-API",
        title="API Tender",
        reference_number="DOC-API",
    )
    upsert_discovered_document(
        db,
        tender_id=tender.id,
        document_name="Tender Document",
        document_url="https://example.test/tender.pdf",
        source_document_id="api-doc-1",
    )
    db.commit()

    async def fake_process(self, tender_id, *, force=False):
        from app.models.tender import TenderDocumentProcessingJob
        from app.core.enums import TenderDocumentProcessingJobStatus

        job = TenderDocumentProcessingJob(
            tender_id=tender_id,
            status=TenderDocumentProcessingJobStatus.COMPLETED,
            discovered=1,
            downloaded=1,
            extracted=1,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job, []

    monkeypatch.setattr(TenderDocumentService, "process_tender_documents", fake_process)
    response = admin_client.post(f"/api/tenders/{tender.id}/process-documents", json={"force": False})
    assert response.status_code == 202
    assert response.json()["discovered"] == 1
