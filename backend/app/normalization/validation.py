"""Validation for normalized tender payloads."""

from __future__ import annotations

from datetime import datetime

from app.core.enums import NormalizationStatus
from app.normalization.models import NormalizedTenderPayload


def validate_normalized_tender(payload: NormalizedTenderPayload) -> list[str]:
    warnings: list[str] = []
    errors: list[str] = []

    if not payload.source_tender_id:
        errors.append("source_tender_id is required")
    if not payload.title:
        errors.append("title is required")
    if not payload.source_url:
        errors.append("source_url is required")

    for field_name, amount in (
        ("estimated_value", payload.estimated_value),
        ("emd_amount", payload.emd_amount),
        ("tender_fee", payload.tender_fee),
    ):
        if amount is not None and amount < 0:
            errors.append(f"{field_name} must be non-negative")

    warnings.extend(_date_consistency_warnings(payload))

    if errors:
        payload.normalization_status = NormalizationStatus.FAILED
        payload.validation_warnings.extend(errors)
    payload.validation_warnings.extend(warnings)
    return errors


def _date_consistency_warnings(payload: NormalizedTenderPayload) -> list[str]:
    warnings: list[str] = []
    if payload.submission_start and payload.submission_end and payload.submission_end < payload.submission_start:
        warnings.append("submission_end is earlier than submission_start")
    if payload.opening_date and payload.submission_start and payload.opening_date < payload.submission_start:
        warnings.append("opening_date is earlier than submission_start")
    if payload.submission_end and payload.status.value == "OPEN":
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        end = payload.submission_end if payload.submission_end.tzinfo else payload.submission_end.replace(tzinfo=UTC)
        if end < now and not payload.source_status:
            warnings.append("submission_end is in the past but normalized status is OPEN")
    return warnings
