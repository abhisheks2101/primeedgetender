"""Company profile business logic."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.company import (
    CapabilityCategory,
    Company,
    CompanyCapability,
    CompanyDocument,
    CompanyExperience,
    CompanyLocation,
    CompanyMachinery,
    CompanyPersonnel,
    CompanyRegistration,
    ContractorRegistration,
    DocumentType,
    FinancialRecord,
)
from app.models.user import User
from app.schemas.company import (
    CompanyCapabilityAssign,
    CompanyCreate,
    CompanySummary,
    CompanyUpdate,
    ContractorRegistrationCreate,
    ContractorRegistrationUpdate,
    ExperienceCreate,
    ExperienceUpdate,
    FinancialRecordCreate,
    FinancialRecordUpdate,
    LocationCreate,
    MachineryCreate,
    MachineryUpdate,
    PersonnelCreate,
    PersonnelUpdate,
    RegistrationCreate,
    RegistrationUpdate,
)


class CompanyService:
    def __init__(self, db: Session):
        self.db = db

    def get_company_or_404(self, company_id: UUID) -> Company:
        company = self.db.get(Company, company_id)
        if company is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found.")
        return company

    def list_companies(self, search: str | None = None, active_only: bool | None = None) -> list[CompanySummary]:
        query = select(Company)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                Company.display_name.ilike(pattern)
                | Company.legal_name.ilike(pattern)
                | Company.city.ilike(pattern)
                | Company.state.ilike(pattern)
            )
        if active_only is not None:
            query = query.where(Company.is_active.is_(active_only))
        companies = self.db.scalars(query.order_by(Company.display_name.asc())).all()

        summaries: list[CompanySummary] = []
        for company in companies:
            summaries.append(
                CompanySummary(
                    id=company.id,
                    legal_name=company.legal_name,
                    display_name=company.display_name,
                    legal_entity_type=company.legal_entity_type,
                    city=company.city,
                    state=company.state,
                    is_active=company.is_active,
                    project_count=self.db.scalar(
                        select(func.count(CompanyExperience.id)).where(
                            CompanyExperience.company_id == company.id,
                            CompanyExperience.is_active.is_(True),
                        )
                    )
                    or 0,
                    registration_count=self.db.scalar(
                        select(func.count(CompanyRegistration.id)).where(
                            CompanyRegistration.company_id == company.id,
                            CompanyRegistration.is_active.is_(True),
                        )
                    )
                    or 0,
                    document_count=self.db.scalar(
                        select(func.count(CompanyDocument.id)).where(
                            CompanyDocument.company_id == company.id,
                            CompanyDocument.is_active.is_(True),
                        )
                    )
                    or 0,
                )
            )
        return summaries

    def create_company(self, payload: CompanyCreate, actor: User) -> Company:
        company = Company(**payload.model_dump(), created_by=actor.id, updated_by=actor.id)
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def update_company(self, company_id: UUID, payload: CompanyUpdate, actor: User) -> Company:
        company = self.get_company_or_404(company_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(company, field, value)
        company.updated_by = actor.id
        self.db.commit()
        self.db.refresh(company)
        return company

    def archive_company(self, company_id: UUID, actor: User) -> Company:
        company = self.get_company_or_404(company_id)
        company.is_active = False
        company.updated_by = actor.id
        self.db.commit()
        self.db.refresh(company)
        return company

    def list_registrations(self, company_id: UUID) -> list[CompanyRegistration]:
        self.get_company_or_404(company_id)
        return self.db.scalars(
            select(CompanyRegistration).where(CompanyRegistration.company_id == company_id).order_by(CompanyRegistration.created_at.desc())
        ).all()

    def create_registration(self, company_id: UUID, payload: RegistrationCreate) -> CompanyRegistration:
        self.get_company_or_404(company_id)
        registration = CompanyRegistration(company_id=company_id, **payload.model_dump())
        self.db.add(registration)
        self.db.commit()
        self.db.refresh(registration)
        return registration

    def update_registration(self, company_id: UUID, registration_id: UUID, payload: RegistrationUpdate) -> CompanyRegistration:
        registration = self._get_child_or_404(CompanyRegistration, company_id, registration_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(registration, field, value)
        self.db.commit()
        self.db.refresh(registration)
        return registration

    def archive_registration(self, company_id: UUID, registration_id: UUID) -> CompanyRegistration:
        registration = self._get_child_or_404(CompanyRegistration, company_id, registration_id)
        registration.is_active = False
        self.db.commit()
        self.db.refresh(registration)
        return registration

    def list_contractor_registrations(self, company_id: UUID) -> list[ContractorRegistration]:
        self.get_company_or_404(company_id)
        return self.db.scalars(
            select(ContractorRegistration)
            .where(ContractorRegistration.company_id == company_id)
            .order_by(ContractorRegistration.created_at.desc())
        ).all()

    def create_contractor_registration(self, company_id: UUID, payload: ContractorRegistrationCreate) -> ContractorRegistration:
        self.get_company_or_404(company_id)
        item = ContractorRegistration(company_id=company_id, **payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_contractor_registration(
        self, company_id: UUID, item_id: UUID, payload: ContractorRegistrationUpdate
    ) -> ContractorRegistration:
        item = self._get_child_or_404(ContractorRegistration, company_id, item_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def archive_contractor_registration(self, company_id: UUID, item_id: UUID) -> ContractorRegistration:
        item = self._get_child_or_404(ContractorRegistration, company_id, item_id)
        item.is_active = False
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_financial_records(self, company_id: UUID) -> list[FinancialRecord]:
        self.get_company_or_404(company_id)
        return self.db.scalars(
            select(FinancialRecord).where(FinancialRecord.company_id == company_id).order_by(FinancialRecord.financial_year.desc())
        ).all()

    def create_financial_record(self, company_id: UUID, payload: FinancialRecordCreate) -> FinancialRecord:
        self.get_company_or_404(company_id)
        item = FinancialRecord(company_id=company_id, **payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_financial_record(self, company_id: UUID, item_id: UUID, payload: FinancialRecordUpdate) -> FinancialRecord:
        item = self._get_child_or_404(FinancialRecord, company_id, item_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def archive_financial_record(self, company_id: UUID, item_id: UUID) -> FinancialRecord:
        item = self._get_child_or_404(FinancialRecord, company_id, item_id)
        item.is_active = False
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_capabilities(self, company_id: UUID) -> list[CompanyCapability]:
        self.get_company_or_404(company_id)
        return self.db.scalars(
            select(CompanyCapability)
            .options(selectinload(CompanyCapability.capability))
            .where(CompanyCapability.company_id == company_id, CompanyCapability.is_active.is_(True))
        ).all()

    def assign_capability(self, company_id: UUID, payload: CompanyCapabilityAssign) -> CompanyCapability:
        self.get_company_or_404(company_id)
        capability = self.db.get(CapabilityCategory, payload.capability_id)
        if capability is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capability not found.")
        existing = self.db.scalar(
            select(CompanyCapability).where(
                CompanyCapability.company_id == company_id,
                CompanyCapability.capability_id == payload.capability_id,
            )
        )
        if existing:
            for field, value in payload.model_dump(exclude={"capability_id"}).items():
                setattr(existing, field, value)
            existing.is_active = True
            self.db.commit()
            self.db.refresh(existing)
            return existing
        item = CompanyCapability(company_id=company_id, **payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return self.db.scalar(
            select(CompanyCapability)
            .options(selectinload(CompanyCapability.capability))
            .where(CompanyCapability.id == item.id)
        )

    def unassign_capability(self, company_id: UUID, capability_link_id: UUID) -> None:
        item = self._get_child_or_404(CompanyCapability, company_id, capability_link_id)
        item.is_active = False
        self.db.commit()

    def list_experiences(self, company_id: UUID) -> list[CompanyExperience]:
        self.get_company_or_404(company_id)
        return self.db.scalars(
            select(CompanyExperience).where(CompanyExperience.company_id == company_id).order_by(CompanyExperience.created_at.desc())
        ).all()

    def get_experience(self, company_id: UUID, experience_id: UUID) -> CompanyExperience:
        return self._get_child_or_404(CompanyExperience, company_id, experience_id)

    def create_experience(self, company_id: UUID, payload: ExperienceCreate, actor: User) -> CompanyExperience:
        self.get_company_or_404(company_id)
        item = CompanyExperience(company_id=company_id, created_by=actor.id, updated_by=actor.id, **payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_experience(self, company_id: UUID, experience_id: UUID, payload: ExperienceUpdate, actor: User) -> CompanyExperience:
        item = self._get_child_or_404(CompanyExperience, company_id, experience_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        item.updated_by = actor.id
        self.db.commit()
        self.db.refresh(item)
        return item

    def archive_experience(self, company_id: UUID, experience_id: UUID, actor: User) -> CompanyExperience:
        item = self._get_child_or_404(CompanyExperience, company_id, experience_id)
        item.is_active = False
        item.updated_by = actor.id
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_machinery(self, company_id: UUID) -> list[CompanyMachinery]:
        self.get_company_or_404(company_id)
        return self.db.scalars(
            select(CompanyMachinery).where(CompanyMachinery.company_id == company_id).order_by(CompanyMachinery.created_at.desc())
        ).all()

    def create_machinery(self, company_id: UUID, payload: MachineryCreate) -> CompanyMachinery:
        self.get_company_or_404(company_id)
        item = CompanyMachinery(company_id=company_id, **payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_machinery(self, company_id: UUID, item_id: UUID, payload: MachineryUpdate) -> CompanyMachinery:
        item = self._get_child_or_404(CompanyMachinery, company_id, item_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def archive_machinery(self, company_id: UUID, item_id: UUID) -> CompanyMachinery:
        item = self._get_child_or_404(CompanyMachinery, company_id, item_id)
        item.is_active = False
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_personnel(self, company_id: UUID) -> list[CompanyPersonnel]:
        self.get_company_or_404(company_id)
        return self.db.scalars(
            select(CompanyPersonnel).where(CompanyPersonnel.company_id == company_id).order_by(CompanyPersonnel.created_at.desc())
        ).all()

    def create_personnel(self, company_id: UUID, payload: PersonnelCreate) -> CompanyPersonnel:
        self.get_company_or_404(company_id)
        item = CompanyPersonnel(company_id=company_id, **payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_personnel(self, company_id: UUID, item_id: UUID, payload: PersonnelUpdate) -> CompanyPersonnel:
        item = self._get_child_or_404(CompanyPersonnel, company_id, item_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def archive_personnel(self, company_id: UUID, item_id: UUID) -> CompanyPersonnel:
        item = self._get_child_or_404(CompanyPersonnel, company_id, item_id)
        item.is_active = False
        self.db.commit()
        self.db.refresh(item)
        return item

    def list_locations(self, company_id: UUID) -> list[CompanyLocation]:
        self.get_company_or_404(company_id)
        return self.db.scalars(
            select(CompanyLocation).where(CompanyLocation.company_id == company_id).order_by(CompanyLocation.created_at.desc())
        ).all()

    def create_location(self, company_id: UUID, payload: LocationCreate) -> CompanyLocation:
        self.get_company_or_404(company_id)
        item = CompanyLocation(company_id=company_id, **payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_location(self, company_id: UUID, item_id: UUID) -> None:
        item = self._get_child_or_404(CompanyLocation, company_id, item_id)
        self.db.delete(item)
        self.db.commit()

    def list_document_types(self) -> list[DocumentType]:
        return self.db.scalars(select(DocumentType).where(DocumentType.is_active.is_(True)).order_by(DocumentType.name.asc())).all()

    def list_capability_categories(self) -> list[CapabilityCategory]:
        return self.db.scalars(
            select(CapabilityCategory).where(CapabilityCategory.is_active.is_(True)).order_by(CapabilityCategory.name.asc())
        ).all()

    def _get_child_or_404(self, model, company_id: UUID, item_id: UUID):
        item = self.db.scalar(select(model).where(model.id == item_id, model.company_id == company_id))
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
        return item
