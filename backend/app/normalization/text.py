"""Text normalization helpers."""

from __future__ import annotations

import re
import unicodedata


def normalize_text(value: str | None) -> str | None:
    """Normalize text for comparison without destroying the original value."""
    if value is None:
        return None
    cleaned = unicodedata.normalize("NFKC", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return None
    return cleaned.casefold()


def normalize_reference(value: str | None) -> str | None:
    normalized = normalize_text(value)
    if normalized is None:
        return None
    return re.sub(r"[^a-z0-9]+", "", normalized)
