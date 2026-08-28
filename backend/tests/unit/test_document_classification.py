"""Unit tests for document classification."""

from app.core.enums import TenderDocumentClassification
from app.document_processing.classification import classify_document


def test_classify_corrigendum():
    assert classify_document(document_name="Corrigendum 1", document_url=None) == TenderDocumentClassification.CORRIGENDUM


def test_classify_boq():
    assert classify_document(document_name="BOQ Sheet", document_url=None) == TenderDocumentClassification.BOQ


def test_classify_unknown():
    assert classify_document(document_name="misc-file", document_url=None) == TenderDocumentClassification.UNKNOWN
