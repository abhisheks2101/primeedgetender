"""Unit tests for status normalization."""

from datetime import UTC, datetime, timedelta

from app.core.enums import TenderStatus
from app.normalization.status import normalize_status


def test_normalize_status_open_variants():
    status, source = normalize_status("Active")
    assert status == TenderStatus.OPEN
    assert source == "Active"


def test_normalize_status_closed_variant():
    status, _ = normalize_status("Closed")
    assert status == TenderStatus.CLOSED


def test_normalize_status_unknown():
    status, _ = normalize_status("Mystery Status")
    assert status == TenderStatus.UNKNOWN


def test_normalize_status_from_future_submission_end():
    future = datetime.now(UTC) + timedelta(days=10)
    status, _ = normalize_status(None, submission_end=future)
    assert status == TenderStatus.OPEN
