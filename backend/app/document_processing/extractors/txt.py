"""Plain text extraction."""

from __future__ import annotations

from app.core.enums import TenderDocumentExtractionMethod
from app.document_processing.extractors.base import ExtractedPage, ExtractionResult


def extract_txt_text(content: bytes) -> ExtractionResult:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("latin-1", errors="replace")
    text = text.strip()
    pages = [ExtractedPage(page_number=1, text=text, extraction_method=TenderDocumentExtractionMethod.DIRECT_EXTRACTION)]
    return ExtractionResult(
        success=True,
        pages=pages,
        page_count=1,
        character_count=len(text),
        extraction_method=TenderDocumentExtractionMethod.DIRECT_EXTRACTION,
        needs_ocr=False,
    )
