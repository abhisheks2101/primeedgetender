"""Document processing pipeline orchestration."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.config import Settings
from app.core.enums import (
    TenderDocumentDownloadStatus,
    TenderDocumentErrorCode,
    TenderDocumentExtractionMethod,
    TenderDocumentExtractionStatus,
    TenderDocumentProcessingEventKind,
    TenderDocumentProcessingStatus,
)
from app.document_processing.checksum import sha256_checksum
from app.document_processing.downloader import DocumentDownloader
from app.document_processing.extractors import extract_document_text
from app.document_processing.file_validation import validate_file_content
from app.document_processing.storage import TenderDocumentStorage
from app.models.tender import TenderDocument, TenderDocumentPage, TenderDocumentProcessingEvent, TenderDocumentProcessingJob

logger = logging.getLogger(__name__)


class DocumentProcessingPipeline:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.storage = TenderDocumentStorage(settings)
        self.downloader = DocumentDownloader(
            timeout_seconds=settings.download_timeout_seconds,
            max_size_bytes=settings.max_document_size_bytes,
            retries=settings.download_retries,
            delay_seconds=settings.download_delay_seconds,
            allowed_domains=settings.allowed_document_domains,
        )

    async def process_document(
        self,
        document: TenderDocument,
        *,
        job: TenderDocumentProcessingJob | None = None,
        force: bool = False,
    ) -> TenderDocument:
        if not force and self._should_skip(document):
            if job:
                job.skipped += 1
            return document

        if not document.document_url:
            self._fail(document, TenderDocumentErrorCode.INVALID_FILE, "Document URL is missing.")
            if job:
                job.failed += 1
            return document

        document.download_status = TenderDocumentDownloadStatus.DOWNLOADING
        self._log_event(job, document, TenderDocumentProcessingEventKind.DOWNLOAD_STARTED, "Download started")

        download = await self.downloader.download(document.document_url)
        if not download.success or not download.content:
            self._handle_download_failure(document, download.error_code, download.error_message, download.access_restricted)
            if job:
                job.failed += 1
            self._log_event(job, document, TenderDocumentProcessingEventKind.DOWNLOAD_FAILED, document.error_message or "Download failed")
            return document

        content = download.content
        checksum = sha256_checksum(content)
        if document.checksum and document.checksum != checksum:
            document.previous_checksum = document.checksum

        extension = self._infer_extension(document.document_url, download.content_type)
        validation = validate_file_content(content, claimed_extension=extension)
        if not validation.is_valid or not validation.detected_type:
            self._fail(
                document,
                validation.error_code or TenderDocumentErrorCode.INVALID_FILE,
                validation.error_message or "Invalid file.",
                processing_status=TenderDocumentProcessingStatus.INVALID,
                download_status=TenderDocumentDownloadStatus.DOWNLOAD_FAILED,
            )
            if job:
                job.failed += 1
            self._log_event(job, document, TenderDocumentProcessingEventKind.FILE_REJECTED, document.error_message or "File rejected")
            return document

        filename = f"document.{validation.extension or extension or 'bin'}"
        try:
            storage_path = self.storage.store_file(str(document.tender_id), str(document.id), filename, content)
        except Exception as exc:
            self._fail(document, TenderDocumentErrorCode.STORAGE_ERROR, str(exc))
            if job:
                job.failed += 1
            return document

        now = datetime.now(UTC)
        document.local_storage_path = storage_path
        document.mime_type = validation.mime_type
        document.file_extension = validation.extension
        document.file_size = len(content)
        document.checksum = checksum
        document.download_status = TenderDocumentDownloadStatus.DOWNLOADED
        document.downloaded_at = now
        document.processing_status = TenderDocumentProcessingStatus.VALIDATED
        document.error_code = None
        document.error_message = None
        if job:
            job.downloaded += 1
        self._log_event(job, document, TenderDocumentProcessingEventKind.DOWNLOAD_COMPLETED, "Download completed")
        self._log_event(job, document, TenderDocumentProcessingEventKind.FILE_VALIDATED, "File validated")

        self._log_event(job, document, TenderDocumentProcessingEventKind.TEXT_EXTRACTION_STARTED, "Text extraction started")
        extraction = extract_document_text(
            content,
            detected_type=validation.detected_type,
            ocr_enabled=self.settings.ocr_enabled,
            ocr_languages=self.settings.ocr_languages,
            ocr_min_text_threshold=self.settings.ocr_min_text_threshold,
        )
        if not extraction.success:
            self._fail(
                document,
                TenderDocumentErrorCode.PARSE_ERROR,
                extraction.error_message or "Text extraction failed.",
                extraction_status=TenderDocumentExtractionStatus.EXTRACTION_FAILED,
            )
            if job:
                job.failed += 1
            self._log_event(job, document, TenderDocumentProcessingEventKind.PROCESSING_FAILED, document.error_message or "Extraction failed")
            return document

        if extraction.extraction_method == TenderDocumentExtractionMethod.OCR and job:
            job.ocr_processed += 1
            self._log_event(job, document, TenderDocumentProcessingEventKind.OCR_COMPLETED, "OCR completed")
        elif extraction.needs_ocr:
            document.extraction_status = TenderDocumentExtractionStatus.OCR_REQUIRED
        else:
            document.extraction_status = TenderDocumentExtractionStatus.TEXT_EXTRACTED

        document.pages.clear()
        manifest_pages: list[dict] = []
        for page in extraction.pages:
            page_row = TenderDocumentPage(
                page_number=page.page_number,
                text=page.text,
                extraction_method=page.extraction_method,
                character_count=len(page.text),
            )
            document.pages.append(page_row)
            manifest_pages.append(
                {
                    "page": page.page_number,
                    "text": page.text,
                    "extraction_method": page.extraction_method.value,
                }
            )

        try:
            document.text_storage_path = self.storage.store_extracted_manifest(
                str(document.tender_id),
                str(document.id),
                manifest_pages,
            )
        except Exception as exc:
            self._fail(document, TenderDocumentErrorCode.STORAGE_ERROR, str(exc))
            if job:
                job.failed += 1
            return document

        document.page_count = extraction.page_count
        document.character_count = extraction.character_count
        document.extraction_method = extraction.extraction_method
        if document.extraction_status != TenderDocumentExtractionStatus.OCR_REQUIRED:
            document.extraction_status = (
                TenderDocumentExtractionStatus.OCR_COMPLETED
                if extraction.extraction_method == TenderDocumentExtractionMethod.OCR
                else TenderDocumentExtractionStatus.TEXT_EXTRACTED
            )
        document.processed_at = now
        if job:
            job.extracted += 1
        self._log_event(job, document, TenderDocumentProcessingEventKind.TEXT_EXTRACTION_COMPLETED, "Text extraction completed")
        self._log_event(job, document, TenderDocumentProcessingEventKind.PROCESSING_COMPLETED, "Processing completed")
        self.storage.cleanup_temp_dir(str(document.tender_id), str(document.id))
        return document

    def _should_skip(self, document: TenderDocument) -> bool:
        return (
            document.download_status == TenderDocumentDownloadStatus.DOWNLOADED
            and document.processing_status == TenderDocumentProcessingStatus.VALIDATED
            and document.extraction_status
            in {
                TenderDocumentExtractionStatus.TEXT_EXTRACTED,
                TenderDocumentExtractionStatus.OCR_COMPLETED,
            }
            and document.local_storage_path
            and document.checksum
        )

    def _handle_download_failure(
        self,
        document: TenderDocument,
        error_code: TenderDocumentErrorCode | None,
        error_message: str | None,
        access_restricted: bool,
    ) -> None:
        if access_restricted:
            document.download_status = TenderDocumentDownloadStatus.ACCESS_RESTRICTED
            error_code = TenderDocumentErrorCode.ACCESS_RESTRICTED
        else:
            document.download_status = TenderDocumentDownloadStatus.DOWNLOAD_FAILED
        self._fail(
            document,
            error_code or TenderDocumentErrorCode.UNKNOWN_ERROR,
            error_message or "Download failed.",
            download_status=document.download_status,
        )

    def _fail(
        self,
        document: TenderDocument,
        error_code: TenderDocumentErrorCode,
        error_message: str,
        *,
        download_status: TenderDocumentDownloadStatus | None = None,
        processing_status: TenderDocumentProcessingStatus = TenderDocumentProcessingStatus.PROCESSING_FAILED,
        extraction_status: TenderDocumentExtractionStatus = TenderDocumentExtractionStatus.EXTRACTION_FAILED,
    ) -> None:
        if download_status is not None:
            document.download_status = download_status
        document.processing_status = processing_status
        document.extraction_status = extraction_status
        document.error_code = error_code
        document.error_message = error_message

    def _infer_extension(self, url: str | None, content_type: str | None) -> str | None:
        if url:
            suffix = Path(urlparse(url).path).suffix.lower().lstrip(".")
            if suffix:
                return suffix
        if content_type:
            lowered = content_type.lower()
            if "pdf" in lowered:
                return "pdf"
            if "html" in lowered:
                return "html"
            if "plain" in lowered:
                return "txt"
            if "wordprocessingml" in lowered:
                return "docx"
        return None

    def _log_event(
        self,
        job: TenderDocumentProcessingJob | None,
        document: TenderDocument,
        kind: TenderDocumentProcessingEventKind,
        message: str,
    ) -> None:
        if job is None:
            return
        self.db.add(
            TenderDocumentProcessingEvent(
                job_id=job.id,
                document_id=document.id,
                kind=kind,
                message=message,
            )
        )
