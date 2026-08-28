"""Monetary value normalization."""

from __future__ import annotations

import logging
import re
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


def normalize_amount(value: Decimal | str | int | float | None) -> tuple[Decimal | None, str | None]:
    if value is None:
        return None, None
    if isinstance(value, Decimal):
        return value, str(value)
    raw = str(value).strip()
    if not raw or raw.upper() in {"NA", "N/A", "-", "--", "NIL"}:
        return None, raw or None
    cleaned = raw.replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
    cleaned = cleaned.replace(",", "")
    if not cleaned or not re.fullmatch(r"\d+(\.\d+)?", cleaned):
        logger.warning("Unable to normalize amount: %s", raw)
        return None, raw
    try:
        return Decimal(cleaned), raw
    except InvalidOperation:
        logger.warning("Invalid decimal amount: %s", raw)
        return None, raw
