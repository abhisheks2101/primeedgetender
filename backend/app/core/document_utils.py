"""Document and file helper utilities."""

import mimetypes
import re
import uuid
from datetime import date, timedelta
from pathlib import Path

from app.core.enums import DocumentStatus

UNSAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]")
BLOCKED_EXTENSIONS = {
    ".exe",
    ".bat",
    ".cmd",
    ".com",
    ".msi",
    ".scr",
    ".ps1",
    ".sh",
    ".js",
    ".jar",
    ".app",
}


def sanitize_filename(filename: str) -> str:
    basename = Path(filename).name
    sanitized = UNSAFE_FILENAME_PATTERN.sub("_", basename).strip("._")
    return sanitized or "upload.bin"


def generate_stored_filename(original_filename: str) -> str:
    extension = Path(original_filename).suffix.lower()
    if extension in BLOCKED_EXTENSIONS:
        extension = ".bin"
    return f"{uuid.uuid4().hex}{extension}"


def detect_mime_type(filename: str, fallback: str = "application/octet-stream") -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or fallback


def validate_upload_file(
    filename: str,
    mime_type: str,
    file_size: int,
    allowed_mime_types: list[str],
    max_file_size_bytes: int,
) -> None:
    extension = Path(filename).suffix.lower()
    if extension in BLOCKED_EXTENSIONS:
        raise ValueError("Executable or unsupported file types are not allowed.")
    if file_size <= 0:
        raise ValueError("Uploaded file is empty.")
    if file_size > max_file_size_bytes:
        raise ValueError(f"File exceeds maximum allowed size of {max_file_size_bytes} bytes.")
    if mime_type not in allowed_mime_types:
        raise ValueError("Unsupported file type.")


def compute_document_status(expiry_date: date | None, expiring_soon_days: int = 30) -> DocumentStatus:
    if expiry_date is None:
        return DocumentStatus.UNKNOWN
    today = date.today()
    if expiry_date < today:
        return DocumentStatus.EXPIRED
    if expiry_date <= today + timedelta(days=expiring_soon_days):
        return DocumentStatus.EXPIRING_SOON
    return DocumentStatus.VALID
