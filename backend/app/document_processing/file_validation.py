"""File signature validation for tender documents."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.enums import TenderDocumentErrorCode


@dataclass(slots=True)
class FileValidationResult:
    is_valid: bool
    detected_type: str | None
    mime_type: str | None
    extension: str | None
    error_code: TenderDocumentErrorCode | None = None
    error_message: str | None = None


def validate_file_content(content: bytes, *, claimed_extension: str | None = None) -> FileValidationResult:
    if not content:
        return FileValidationResult(
            is_valid=False,
            detected_type=None,
            mime_type=None,
            extension=claimed_extension,
            error_code=TenderDocumentErrorCode.INVALID_FILE,
            error_message="Empty file content.",
        )

    if content.startswith(b"MZ"):
        return FileValidationResult(
            is_valid=False,
            detected_type="exe",
            mime_type="application/x-msdownload",
            extension=claimed_extension,
            error_code=TenderDocumentErrorCode.UNSUPPORTED_FILE,
            error_message="Executable files are not supported.",
        )

    if content.startswith(b"%PDF"):
        return FileValidationResult(True, "pdf", "application/pdf", "pdf")

    if content.startswith(b"PK\x03\x04"):
        if claimed_extension == "docx":
            return FileValidationResult(True, "docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx")
        return FileValidationResult(
            is_valid=False,
            detected_type="zip",
            mime_type="application/zip",
            extension=claimed_extension,
            error_code=TenderDocumentErrorCode.UNSUPPORTED_FILE,
            error_message="Unsupported archive format.",
        )

    lowered = content[:512].lower()
    if b"<html" in lowered or b"<!doctype html" in lowered:
        if claimed_extension in {"html", "htm", None}:
            return FileValidationResult(True, "html", "text/html", claimed_extension or "html")
        return FileValidationResult(
            is_valid=False,
            detected_type="html",
            mime_type="text/html",
            extension=claimed_extension,
            error_code=TenderDocumentErrorCode.INVALID_FILE,
            error_message="HTML content does not match claimed file type.",
        )

    if claimed_extension in {"txt", "text"} or _looks_like_text(content):
        return FileValidationResult(True, "txt", "text/plain", "txt")

    return FileValidationResult(
        is_valid=False,
        detected_type=None,
        mime_type=None,
        extension=claimed_extension,
        error_code=TenderDocumentErrorCode.UNSUPPORTED_FILE,
        error_message="Unsupported or unrecognized file format.",
    )


def _looks_like_text(content: bytes) -> bool:
    sample = content[:4096]
    if not sample:
        return False
    try:
        sample.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False
