"""Document identity helpers."""

from __future__ import annotations

import hashlib
from urllib.parse import urlparse
from uuid import UUID


def resolve_source_document_id(
    *,
    document_id: str | None,
    document_name: str | None,
    document_url: str | None,
    tender_id: UUID,
) -> str:
    if document_id and document_id.strip():
        return document_id.strip()
    parts = [str(tender_id)]
    if document_url:
        parts.append(document_url.strip())
    if document_name:
        parts.append(document_name.strip())
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:32]
    return f"fallback-{digest}"
