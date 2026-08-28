"""Optional OCR fallback for scanned PDFs."""

from __future__ import annotations

import logging
import shutil

from app.core.enums import TenderDocumentExtractionMethod
from app.document_processing.extractors.base import ExtractedPage, ExtractionResult
from app.document_processing.extractors.pdf import extract_pdf_text

logger = logging.getLogger(__name__)


def is_ocr_available() -> bool:
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        return False
    return shutil.which("tesseract") is not None


def ocr_pdf(content: bytes, *, languages: str) -> ExtractionResult:
    if not is_ocr_available():
        return ExtractionResult(False, pages=[], error_message="Tesseract OCR is not available.")

    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        return ExtractionResult(False, pages=[], error_message=f"OCR dependencies unavailable: {exc}")

    pages: list[ExtractedPage] = []
    try:
        document = fitz.open(stream=content, filetype="pdf")
        for index in range(document.page_count):
            page = document.load_page(index)
            pix = page.get_pixmap()
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(image, lang=languages) or ""
            pages.append(
                ExtractedPage(
                    page_number=index + 1,
                    text=text.strip(),
                    extraction_method=TenderDocumentExtractionMethod.OCR,
                )
            )
        document.close()
    except Exception as exc:
        logger.warning("OCR failed: %s", exc)
        return ExtractionResult(False, pages=[], error_message=str(exc))

    character_count = sum(len(page.text) for page in pages)
    return ExtractionResult(
        success=True,
        pages=pages,
        page_count=len(pages),
        character_count=character_count,
        extraction_method=TenderDocumentExtractionMethod.OCR,
        needs_ocr=False,
    )


def extract_with_optional_ocr(
    content: bytes,
    *,
    detected_type: str,
    ocr_enabled: bool,
    ocr_languages: str,
    ocr_min_text_threshold: int,
) -> ExtractionResult:
    if detected_type != "pdf":
        return ExtractionResult(False, pages=[], error_message="OCR is only supported for PDF files.")

    direct = extract_pdf_text(content)
    if not direct.success:
        return direct
    if direct.character_count >= ocr_min_text_threshold or not ocr_enabled:
        return direct

    ocr_result = ocr_pdf(content, languages=ocr_languages)
    if ocr_result.success and ocr_result.character_count > direct.character_count:
        return ocr_result
    direct.needs_ocr = True
    return direct
