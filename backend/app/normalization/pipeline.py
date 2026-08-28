"""Normalization pipeline orchestration."""

from __future__ import annotations

from app.collectors.base import NormalizedTenderDraft
from app.core.enums import NormalizationStatus
from app.normalization.config import CURRENT_NORMALIZATION_VERSION
from app.normalization.dates import normalize_datetime
from app.normalization.location import normalize_location
from app.normalization.models import NormalizedTenderPayload
from app.normalization.money import normalize_amount
from app.normalization.status import normalize_status
from app.normalization.text import normalize_text
from app.normalization.validation import validate_normalized_tender


def normalize_draft(draft: NormalizedTenderDraft, *, source_code: str) -> NormalizedTenderPayload:
    location_data = normalize_location(
        draft.location,
        state=draft.state,
        district=draft.district,
        source_code=source_code,
    )
    publication_date, _ = normalize_datetime(draft.publication_date)
    document_sale_start, _ = normalize_datetime(draft.document_sale_start)
    document_sale_end, _ = normalize_datetime(draft.document_sale_end)
    submission_start, _ = normalize_datetime(draft.submission_start)
    submission_end, _ = normalize_datetime(draft.submission_end)
    opening_date, _ = normalize_datetime(draft.opening_date)
    estimated_value, _ = normalize_amount(draft.estimated_value)
    emd_amount, _ = normalize_amount(draft.emd_amount)
    tender_fee, _ = normalize_amount(draft.tender_fee)
    status, source_status = normalize_status(
        draft.status,
        source_status=draft.source_status,
        submission_end=submission_end,
    )

    payload = NormalizedTenderPayload(
        source_tender_id=draft.source_tender_id,
        reference_number=draft.reference_number,
        title=draft.title,
        work_description=draft.work_description,
        organization=draft.organization,
        department=draft.department,
        tender_type=draft.tender_type,
        tender_category=draft.tender_category,
        location=location_data["location"],
        district=location_data["district"],
        state=location_data["state"],
        state_code=location_data["state_code"],
        original_location_text=location_data["original_location_text"],
        estimated_value=estimated_value,
        emd_amount=emd_amount,
        tender_fee=tender_fee,
        publication_date=publication_date,
        document_sale_start=document_sale_start,
        document_sale_end=document_sale_end,
        submission_start=submission_start,
        submission_end=submission_end,
        opening_date=opening_date,
        status=status,
        source_status=source_status,
        source_url=draft.source_url,
        source_last_updated=draft.source_last_updated,
        title_normalized=normalize_text(draft.title),
        description_normalized=normalize_text(draft.work_description),
        organization_normalized=normalize_text(draft.organization),
        normalization_version=CURRENT_NORMALIZATION_VERSION,
        normalization_status=NormalizationStatus.NORMALIZED,
    )

    errors = validate_normalized_tender(payload)
    if errors:
        payload.normalization_status = NormalizationStatus.FAILED
    elif payload.validation_warnings:
        payload.normalization_status = NormalizationStatus.NEEDS_REVIEW

    return payload
