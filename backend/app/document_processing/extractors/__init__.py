"""Dispatch text extraction by detected file type."""

from __future__ import annotations

from app.document_processing.extractors.base import ExtractionResult
from app.document_processing.extractors.docx import extract_docx_text
from app.document_processing.extractors.html import extract_html_text
from app.document_processing.extractors.pdf import extract_pdf_text
from app.document_processing.extractors.txt import extract_txt_text
from app.document_processing.ocr import extract_with_optional_ocr


def extract_document_text(
    content: bytes,
    *,
    detected_type: str,
    ocr_enabled: bool,
    ocr_languages: str,
    ocr_min_text_threshold: int,
) -> ExtractionResult:
    if detected_type == "pdf":
        return extract_with_optional_ocr(
            content,
            detected_type=detected_type,
            ocr_enabled=ocr_enabled,
            ocr_languages=ocr_languages,
            ocr_min_text_threshold=ocr_min_text_threshold,
        )
    if detected_type == "txt":
        return extract_txt_text(content)
    if detected_type == "html":
        return extract_html_text(content)
    if detected_type == "docx":
        return extract_docx_text(content)
    return ExtractionResult(False, pages=[], error_message=f"Unsupported file type: {detected_type}")
