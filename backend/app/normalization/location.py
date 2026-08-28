"""Location and state normalization."""

from __future__ import annotations

import re

from app.core.enums import IndianStateCode
from app.normalization.text import normalize_text

STATE_ALIASES: dict[str, IndianStateCode] = {
    "uttar pradesh": IndianStateCode.UTTAR_PRADESH,
    "up": IndianStateCode.UTTAR_PRADESH,
    "u p": IndianStateCode.UTTAR_PRADESH,
    "madhya pradesh": IndianStateCode.MADHYA_PRADESH,
    "mp": IndianStateCode.MADHYA_PRADESH,
    "m p": IndianStateCode.MADHYA_PRADESH,
}


def normalize_state(value: str | None, *, source_code: str | None = None) -> tuple[IndianStateCode, str | None]:
    cleaned = normalize_text(value)
    if cleaned:
        compact = cleaned.replace(".", "").replace(" ", "")
        for alias, code in STATE_ALIASES.items():
            alias_compact = alias.replace(" ", "")
            if alias in cleaned or compact == alias_compact or cleaned == alias.replace(" ", ""):
                display = code.value.replace("_", " ").title()
                return code, display
        if "uttar pradesh" in cleaned:
            return IndianStateCode.UTTAR_PRADESH, "Uttar Pradesh"
        if "madhya pradesh" in cleaned:
            return IndianStateCode.MADHYA_PRADESH, "Madhya Pradesh"

    if source_code == "UP_TENDER":
        return IndianStateCode.UTTAR_PRADESH, "Uttar Pradesh"
    if source_code == "MP_TENDER":
        return IndianStateCode.MADHYA_PRADESH, "Madhya Pradesh"
    return IndianStateCode.UNKNOWN, value.strip() if value else None


def normalize_location(
    location: str | None,
    *,
    state: str | None = None,
    district: str | None = None,
    source_code: str | None = None,
) -> dict[str, str | IndianStateCode | None]:
    original = location.strip() if location else None
    state_code, state_display = normalize_state(state or location, source_code=source_code)
    district_value = district
    location_value = original
    if original and "," in original:
        parts = [part.strip() for part in original.split(",") if part.strip()]
        if parts and not district_value:
            district_value = parts[0]
        if len(parts) > 1 and state_code == IndianStateCode.UNKNOWN:
            state_code, state_display = normalize_state(parts[-1], source_code=source_code)
    elif original and not district_value:
        district_value = original
    return {
        "location": location_value,
        "district": district_value,
        "state": state_display,
        "state_code": state_code,
        "original_location_text": original,
    }
