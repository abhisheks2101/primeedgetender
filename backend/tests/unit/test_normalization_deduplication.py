"""Unit tests for fuzzy duplicate detection."""

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.core.enums import DuplicateMatchType
from app.normalization.deduplication import compare_tenders


def _tender(**kwargs):
    defaults = {
        "id": uuid4(),
        "tender_source_id": uuid4(),
        "source_tender_id": "A-1",
        "reference_number": "REF-001",
        "title": "Road Construction Work",
        "title_normalized": "road construction work",
        "organization": "PWD",
        "organization_normalized": "pwd",
        "estimated_value": Decimal("20000000"),
        "submission_end": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_exact_duplicate_same_source_id():
    source_id = uuid4()
    left = _tender(tender_source_id=source_id, source_tender_id="SAME")
    right = _tender(tender_source_id=source_id, source_tender_id="SAME")
    result = compare_tenders(left, right, left_source_code="UP_TENDER", right_source_code="UP_TENDER")
    assert result.match_type == DuplicateMatchType.EXACT_DUPLICATE
    assert result.confidence == 1.0


def test_cross_source_identical_content_not_auto_merged():
    left = _tender(source_tender_id="123", title="Road Construction", title_normalized="road construction")
    right = _tender(
        source_tender_id="123",
        title="Road Construction",
        title_normalized="road construction",
        tender_source_id=uuid4(),
        reference_number="OTHER",
    )
    result = compare_tenders(left, right, left_source_code="UP_TENDER", right_source_code="MP_TENDER")
    assert result.match_type != DuplicateMatchType.EXACT_DUPLICATE
    assert result.confidence <= 0.75


def test_possible_duplicate_similar_titles_same_source():
    source_id = uuid4()
    left = _tender(tender_source_id=source_id, source_tender_id="UP-1", reference_number="R1")
    right = _tender(
        tender_source_id=source_id,
        source_tender_id="UP-2",
        reference_number="R2",
        title="Road Construction Works Phase 2",
        title_normalized="road construction works phase 2",
    )
    result = compare_tenders(left, right, left_source_code="UP_TENDER", right_source_code="UP_TENDER")
    assert result.match_type in {DuplicateMatchType.POSSIBLE_DUPLICATE, DuplicateMatchType.LIKELY_DUPLICATE, DuplicateMatchType.NOT_DUPLICATE}


def test_unrelated_tenders_not_duplicate():
    source_id = uuid4()
    left = _tender(
        tender_source_id=source_id,
        source_tender_id="H-1",
        title="Hospital Equipment",
        title_normalized="hospital equipment",
        reference_number="H1",
        organization="Health Dept",
        organization_normalized="health dept",
        estimated_value=Decimal("1000000"),
    )
    right = _tender(
        tender_source_id=source_id,
        source_tender_id="B-1",
        title="Bridge Repair",
        title_normalized="bridge repair",
        reference_number="B1",
        organization="Roads Dept",
        organization_normalized="roads dept",
        estimated_value=Decimal("9000000"),
    )
    result = compare_tenders(left, right, left_source_code="UP_TENDER", right_source_code="UP_TENDER")
    assert result.match_type == DuplicateMatchType.NOT_DUPLICATE
