"""DOCX text extraction."""

from __future__ import annotations

import io

from docx import Document

from app.core.enums import TenderDocumentExtractionMethod
from app.document_processing.extractors.base import ExtractedPage, ExtractionResult


def extract_docx_text(content: bytes) -> ExtractionResult:
    try:
        document = Document(io.BytesIO(content))
    except Exception as exc:
        return ExtractionResult(False, pages=[], error_message=f"Unable to open DOCX: {exc}")

    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    text = "\n".join(paragraphs)
    pages = [ExtractedPage(page_number=1, text=text, extraction_method=TenderDocumentExtractionMethod.DIRECT_EXTRACTION)]
    return ExtractionResult(
        success=True,
        pages=pages,
        page_count=1,
        character_count=len(text),
        extraction_method=TenderDocumentExtractionMethod.DIRECT_EXTRACTION,
        needs_ocr=False,
    )
