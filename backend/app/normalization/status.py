"""Status normalization helpers."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.enums import TenderStatus
from app.normalization.text import normalize_text


def normalize_status(
    status: TenderStatus | str | None,
    *,
    source_status: str | None = None,
    submission_end: datetime | None = None,
    now: datetime | None = None,
) -> tuple[TenderStatus, str | None]:
    preserved = source_status.strip() if source_status else None
    if isinstance(status, TenderStatus):
        normalized = status
    elif isinstance(status, str):
        if preserved is None:
            preserved = status.strip() or None
        normalized = _map_source_status(status)
    else:
        normalized = TenderStatus.UNKNOWN

    if preserved:
        mapped = _map_source_status(preserved)
        if mapped != TenderStatus.UNKNOWN:
            normalized = mapped

    if normalized == TenderStatus.UNKNOWN and submission_end is not None:
        current = now or datetime.now(UTC)
        end = submission_end if submission_end.tzinfo else submission_end.replace(tzinfo=UTC)
        normalized = TenderStatus.OPEN if end >= current else TenderStatus.CLOSED

    return normalized, preserved


def _map_source_status(value: str) -> TenderStatus:
    cleaned = normalize_text(value)
    if cleaned is None:
        return TenderStatus.UNKNOWN
    if any(token in cleaned for token in ("cancel", "withdrawn")):
        return TenderStatus.CANCELLED
    if "award" in cleaned:
        return TenderStatus.AWARDED
    if any(token in cleaned for token in ("close", "closed", "expired")):
        return TenderStatus.CLOSED
    if any(token in cleaned for token in ("open", "active", "live", "invitation for bid", "published")):
        return TenderStatus.OPEN
    return TenderStatus.UNKNOWN
