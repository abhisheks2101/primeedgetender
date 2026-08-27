"""Integration test fixtures."""

import pytest
from sqlalchemy import delete

from app.models.company import (
    Company,
    CompanyCapability,
    CompanyDocument,
    CompanyExperience,
    CompanyLocation,
    CompanyMachinery,
    CompanyPersonnel,
    CompanyRegistration,
    ContractorRegistration,
    FinancialRecord,
)
from app.models.tender import Tender, TenderDocument
from app.models.tender_source import (
    TenderCollectionEvent,
    TenderCollectionJob,
    TenderRawRecord,
    TenderSource,
)
from app.models.user import LoginAttempt, User, UserSession


@pytest.fixture(autouse=True)
def clean_integration_tables(db):
    db.execute(delete(TenderDocument))
    db.execute(delete(Tender))
    db.execute(delete(TenderRawRecord))
    db.execute(delete(TenderCollectionEvent))
    db.execute(delete(TenderCollectionJob))
    db.execute(delete(TenderSource))
    db.execute(delete(CompanyDocument))
    db.execute(delete(CompanyCapability))
    db.execute(delete(CompanyExperience))
    db.execute(delete(CompanyMachinery))
    db.execute(delete(CompanyPersonnel))
    db.execute(delete(CompanyLocation))
    db.execute(delete(FinancialRecord))
    db.execute(delete(ContractorRegistration))
    db.execute(delete(CompanyRegistration))
    db.execute(delete(Company))
    db.execute(delete(LoginAttempt))
    db.execute(delete(UserSession))
    db.execute(delete(User))
    db.commit()
    yield
