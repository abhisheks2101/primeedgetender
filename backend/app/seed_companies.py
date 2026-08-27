"""Optional development seed data for company profiles."""

from decimal import Decimal

from app.config import Settings
from app.core.database import create_db_engine, create_session_factory
from app.core.enums import FinancialRecordType, ProjectStatus, RegistrationStatus
from app.models.company import (
    CapabilityCategory,
    Company,
    CompanyCapability,
    CompanyExperience,
    CompanyRegistration,
    FinancialRecord,
)
from app.schemas.company import CompanyCreate
from app.services.company_service import CompanyService
from sqlalchemy import select


class _SeedActor:
    id = None


def seed_demo_companies(settings: Settings | None = None) -> int:
    settings = settings or Settings()
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)

    with session_factory() as db:
        existing = db.scalar(select(Company.id).where(Company.display_name.like("Demo Company %")).limit(1))
        if existing:
            print("Demo company seed data already exists.")
            return 0

        service = CompanyService(db)
        road = db.scalar(select(CapabilityCategory).where(CapabilityCategory.code == "ROAD_CONSTRUCTION"))
        drainage = db.scalar(select(CapabilityCategory).where(CapabilityCategory.code == "DRAINAGE"))

        company_a = service.create_company(
            CompanyCreate(
                legal_name="Demo Company A Infrastructure Private Limited",
                display_name="Demo Company A",
                legal_entity_type="Private Limited",
                city="Lucknow",
                district="Lucknow",
                state="Uttar Pradesh",
                email="demo-a@example.com",
                description="DEVELOPMENT/DEMO DATA ONLY",
            ),
            actor=_SeedActor(),
        )
        company_b = service.create_company(
            CompanyCreate(
                legal_name="Demo Company B Civil Contractors",
                display_name="Demo Company B",
                legal_entity_type="Partnership",
                city="Bhopal",
                district="Bhopal",
                state="Madhya Pradesh",
                email="demo-b@example.com",
                description="DEVELOPMENT/DEMO DATA ONLY",
            ),
            actor=_SeedActor(),
        )

        db.add(
            CompanyRegistration(
                company_id=company_a.id,
                registration_type="GST",
                registration_number="DEMOGSTA001",
                status=RegistrationStatus.ACTIVE,
            )
        )
        db.add(
            FinancialRecord(
                company_id=company_a.id,
                record_type=FinancialRecordType.TURNOVER,
                amount=Decimal("45000000.00"),
                financial_year="2024-25",
            )
        )
        db.add(
            CompanyExperience(
                company_id=company_a.id,
                project_name="Demo CC Road Project",
                work_category="ROAD_CONSTRUCTION",
                subcategory="CONCRETE_ROAD",
                state="Uttar Pradesh",
                project_status=ProjectStatus.COMPLETED,
            )
        )
        if road:
            db.add(CompanyCapability(company_id=company_a.id, capability_id=road.id, years_of_experience=5))
        if drainage:
            db.add(CompanyCapability(company_id=company_b.id, capability_id=drainage.id, years_of_experience=3))

        db.commit()
        print("Seeded demo companies A and B.")
        return 0
