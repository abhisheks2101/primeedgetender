"""Fuzzy duplicate detection."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from app.core.enums import DuplicateMatchType
from app.models.tender import Tender
from app.normalization.config import DEFAULT_THRESHOLDS, DeduplicationThresholds
from app.normalization.text import normalize_reference, normalize_text


@dataclass(slots=True)
class DuplicateComparisonResult:
    match_type: DuplicateMatchType
    confidence: float
    matched_fields: list[str]


def compare_tenders(
    left: Tender,
    right: Tender,
    *,
    left_source_code: str,
    right_source_code: str,
    thresholds: DeduplicationThresholds = DEFAULT_THRESHOLDS,
) -> DuplicateComparisonResult:
    if left.id == right.id:
        return DuplicateComparisonResult(DuplicateMatchType.NOT_DUPLICATE, 0.0, [])

    same_source = left.tender_source_id == right.tender_source_id
    if same_source and left.source_tender_id == right.source_tender_id:
        return DuplicateComparisonResult(DuplicateMatchType.EXACT_DUPLICATE, 1.0, ["source_tender_id"])

    matched_fields: list[str] = []
    scores: list[float] = []

    left_ref = normalize_reference(left.reference_number)
    right_ref = normalize_reference(right.reference_number)
    if left_ref and right_ref and left_ref == right_ref:
        matched_fields.append("reference_number")
        scores.append(1.0)

    title_score = _similarity(left.title_normalized or left.title, right.title_normalized or right.title)
    if title_score >= thresholds.possible_threshold:
        matched_fields.append("title")
        scores.append(title_score)

    org_score = _similarity(left.organization_normalized or left.organization, right.organization_normalized or right.organization)
    if org_score >= thresholds.possible_threshold:
        matched_fields.append("organization")
        scores.append(org_score)

    if left.estimated_value is not None and right.estimated_value is not None and left.estimated_value == right.estimated_value:
        matched_fields.append("estimated_value")
        scores.append(1.0)

    if left.submission_end and right.submission_end and left.submission_end.date() == right.submission_end.date():
        matched_fields.append("submission_end")
        scores.append(1.0)

    if not scores:
        return DuplicateComparisonResult(DuplicateMatchType.NOT_DUPLICATE, 0.0, [])

    confidence = sum(scores) / len(scores)
    if not same_source:
        confidence = min(confidence, thresholds.cross_source_max_confidence)
        if confidence < thresholds.possible_threshold:
            return DuplicateComparisonResult(DuplicateMatchType.NOT_DUPLICATE, confidence, matched_fields)

    if confidence >= thresholds.exact_threshold and same_source and left_ref and left_ref == right_ref:
        return DuplicateComparisonResult(DuplicateMatchType.EXACT_DUPLICATE, confidence, matched_fields)
    if confidence >= thresholds.likely_threshold and same_source:
        return DuplicateComparisonResult(DuplicateMatchType.LIKELY_DUPLICATE, confidence, matched_fields)
    if confidence >= thresholds.possible_threshold:
        return DuplicateComparisonResult(DuplicateMatchType.POSSIBLE_DUPLICATE, confidence, matched_fields)
    return DuplicateComparisonResult(DuplicateMatchType.NOT_DUPLICATE, confidence, matched_fields)


def _similarity(left: str | None, right: str | None) -> float:
    left_norm = normalize_text(left)
    right_norm = normalize_text(right)
    if not left_norm or not right_norm:
        return 0.0
    return SequenceMatcher(None, left_norm, right_norm).ratio()
