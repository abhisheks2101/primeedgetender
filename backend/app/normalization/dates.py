"""Date normalization helpers."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

DATE_FORMATS = (
    "%d-%b-%Y %I:%M %p",
    "%d-%b-%Y %H:%M",
    "%d-%b-%Y",
    "%d/%m/%Y %I:%M %p",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
)


def normalize_datetime(value: datetime | str | None) -> tuple[datetime | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, datetime):
        parsed = value if value.tzinfo else value.replace(tzinfo=UTC)
        return parsed, value.isoformat()
    cleaned = str(value).strip()
    if not cleaned or cleaned.upper() in {"NA", "N/A", "-", "--"}:
        return None, cleaned or None
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed, cleaned
        except ValueError:
            continue
    logger.warning("Unable to normalize date: %s", cleaned)
    return None, cleaned
