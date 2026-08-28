"""Extracted page representation."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.enums import TenderDocumentExtractionMethod


@dataclass(slots=True)
class ExtractedPage:
    page_number: int
    text: str
    extraction_method: TenderDocumentExtractionMethod


@dataclass(slots=True)
class ExtractionResult:
    success: bool
    pages: list[ExtractedPage]
    page_count: int = 0
    character_count: int = 0
    extraction_method: TenderDocumentExtractionMethod = TenderDocumentExtractionMethod.DIRECT_EXTRACTION
    needs_ocr: bool = False
    error_message: str | None = None
