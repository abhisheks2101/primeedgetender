"""Deterministic tender document classification."""

from __future__ import annotations

import re

from app.core.enums import TenderDocumentClassification

_CLASSIFICATION_RULES: tuple[tuple[re.Pattern[str], TenderDocumentClassification], ...] = (
    (re.compile(r"\bnit\b|\bnotice inviting tender\b", re.I), TenderDocumentClassification.NIT),
    (re.compile(r"\bboq\b|\bbill of quantities\b", re.I), TenderDocumentClassification.BOQ),
    (re.compile(r"\bcorrigendum\b|\bcorrigenda\b", re.I), TenderDocumentClassification.CORRIGENDUM),
    (re.compile(r"\baddendum\b|\bamendment\b", re.I), TenderDocumentClassification.ADDENDUM),
    (re.compile(r"\beligibility\b", re.I), TenderDocumentClassification.ELIGIBILITY_DOCUMENT),
    (re.compile(r"\bterms?\s+and\s+conditions?\b|\bgcc\b|\bscc\b", re.I), TenderDocumentClassification.TERMS_AND_CONDITIONS),
    (re.compile(r"\bdrawing\b|\bplan\b", re.I), TenderDocumentClassification.DRAWING),
    (re.compile(r"\btender\b", re.I), TenderDocumentClassification.TENDER_DOCUMENT),
)


def classify_document(
  *,
  document_name: str | None,
  document_url: str | None,
  source_document_type: str | None = None,
) -> TenderDocumentClassification:
    haystack = " ".join(filter(None, [source_document_type, document_name, document_url]))
    if not haystack.strip():
        return TenderDocumentClassification.UNKNOWN
    for pattern, classification in _CLASSIFICATION_RULES:
        if pattern.search(haystack):
            return classification
    if source_document_type:
        return TenderDocumentClassification.OTHER
    return TenderDocumentClassification.UNKNOWN
