"""HTML text extraction."""

from __future__ import annotations

from bs4 import BeautifulSoup

from app.core.enums import TenderDocumentExtractionMethod
from app.document_processing.extractors.base import ExtractedPage, ExtractionResult


def extract_html_text(content: bytes) -> ExtractionResult:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    pages = [ExtractedPage(page_number=1, text=text, extraction_method=TenderDocumentExtractionMethod.DIRECT_EXTRACTION)]
    return ExtractionResult(
        success=True,
        pages=pages,
        page_count=1,
        character_count=len(text),
        extraction_method=TenderDocumentExtractionMethod.DIRECT_EXTRACTION,
        needs_ocr=False,
    )
