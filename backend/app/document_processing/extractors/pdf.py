"""PDF text extraction using PyMuPDF."""

from __future__ import annotations

import io

import fitz

from app.core.enums import TenderDocumentExtractionMethod
from app.document_processing.extractors.base import ExtractedPage, ExtractionResult


def extract_pdf_text(content: bytes) -> ExtractionResult:
    try:
        document = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        return ExtractionResult(False, pages=[], error_message=f"Unable to open PDF: {exc}")

    pages: list[ExtractedPage] = []
    try:
        for index in range(document.page_count):
            page = document.load_page(index)
            text = page.get_text("text") or ""
            pages.append(
                ExtractedPage(
                    page_number=index + 1,
                    text=text.strip(),
                    extraction_method=TenderDocumentExtractionMethod.DIRECT_EXTRACTION,
                )
            )
    finally:
        document.close()

    character_count = sum(len(page.text) for page in pages)
    return ExtractionResult(
        success=True,
        pages=pages,
        page_count=len(pages),
        character_count=character_count,
        extraction_method=TenderDocumentExtractionMethod.DIRECT_EXTRACTION,
        needs_ocr=character_count == 0,
    )
