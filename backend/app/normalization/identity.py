"""Tender identity resolution."""

from __future__ import annotations

from app.normalization.text import normalize_reference


def resolve_identity_key(*, source_code: str, source_tender_id: str, reference_number: str | None) -> str:
    tender_id = (source_tender_id or "").strip()
    if tender_id:
        return f"{source_code}:{tender_id}"
    reference = normalize_reference(reference_number)
    if reference:
        return f"{source_code}:ref:{reference}"
    raise ValueError("Unable to resolve tender identity without source_tender_id or reference_number.")
