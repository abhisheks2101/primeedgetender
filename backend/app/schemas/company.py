"""Pydantic schemas for company profile management."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import (
    DocumentEntityType,
    DocumentStatus,
    FinancialRecordType,
    OwnershipType,
    ProjectStatus,
    RegistrationStatus,
)


class CompanyBase(BaseModel):
    legal_name: str = Field(min_length=1, max_length=500)
    display_name: str = Field(min_length=1, max_length=500)
    legal_entity_type: str | None = None
    registration_number: str | None = None
    incorporation_date: date | None = None
    description: str | None = None
    registered_address: str | None = None
    office_address: str | None = None
    city: str | None = None
    district: str | None = None
    state: str | None = None
    pin_code: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    website: str | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    legal_name: str | None = Field(default=None, min_length=1, max_length=500)
    display_name: str | None = Field(default=None, min_length=1, max_length=500)
    legal_entity_type: str | None = None
    registration_number: str | None = None
    incorporation_date: date | None = None
    description: str | None = None
    registered_address: str | None = None
    office_address: str | None = None
    city: str | None = None
    district: str | None = None
    state: str | None = None
    pin_code: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    website: str | None = None
    is_active: bool | None = None


class CompanySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    legal_name: str
    display_name: str
    legal_entity_type: str | None = None
    city: str | None = None
    state: str | None = None
    is_active: bool
    project_count: int = 0
    registration_count: int = 0
    document_count: int = 0


class CompanyPublic(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RegistrationCreate(BaseModel):
    registration_type: str = Field(min_length=1, max_length=100)
    registration_number: str | None = None
    registration_class: str | None = None
    issuing_authority: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    status: RegistrationStatus = RegistrationStatus.UNKNOWN
    notes: str | None = None


class RegistrationUpdate(BaseModel):
    registration_type: str | None = Field(default=None, min_length=1, max_length=100)
    registration_number: str | None = None
    registration_class: str | None = None
    issuing_authority: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    status: RegistrationStatus | None = None
    notes: str | None = None
    is_active: bool | None = None


class RegistrationPublic(RegistrationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ContractorRegistrationCreate(BaseModel):
    department: str | None = None
    registration_authority: str | None = None
    registration_number: str | None = None
    class_category: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    status: RegistrationStatus = RegistrationStatus.UNKNOWN
    notes: str | None = None


class ContractorRegistrationUpdate(BaseModel):
    department: str | None = None
    registration_authority: str | None = None
    registration_number: str | None = None
    class_category: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    status: RegistrationStatus | None = None
    notes: str | None = None
    is_active: bool | None = None


class ContractorRegistrationPublic(ContractorRegistrationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class FinancialRecordCreate(BaseModel):
    record_type: FinancialRecordType
    amount: Decimal = Field(gt=0)
    currency: str = "INR"
    financial_year: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    as_of_date: date | None = None
    description: str | None = None


class FinancialRecordUpdate(BaseModel):
    record_type: FinancialRecordType | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    currency: str | None = None
    financial_year: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    as_of_date: date | None = None
    description: str | None = None
    is_active: bool | None = None


class FinancialRecordPublic(FinancialRecordCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CapabilityCategoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    category: str | None = None
    description: str | None = None


class CompanyCapabilityAssign(BaseModel):
    capability_id: UUID
    years_of_experience: int | None = Field(default=None, ge=0)
    experience_level: str | None = None
    notes: str | None = None
    completed_projects_count: int | None = Field(default=None, ge=0)
    total_project_value: Decimal | None = Field(default=None, ge=0)


class CompanyCapabilityPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    capability_id: UUID
    capability: CapabilityCategoryPublic
    years_of_experience: int | None = None
    experience_level: str | None = None
    notes: str | None = None
    completed_projects_count: int | None = None
    total_project_value: Decimal | None = None
    is_active: bool


class ExperienceCreate(BaseModel):
    project_name: str = Field(min_length=1, max_length=500)
    client_department: str | None = None
    authority_organization: str | None = None
    work_category: str | None = None
    subcategory: str | None = None
    location: str | None = None
    district: str | None = None
    state: str | None = None
    contract_value: Decimal | None = Field(default=None, ge=0)
    awarded_value: Decimal | None = Field(default=None, ge=0)
    completion_value: Decimal | None = Field(default=None, ge=0)
    start_date: date | None = None
    completion_date: date | None = None
    project_status: ProjectStatus = ProjectStatus.UNKNOWN
    description: str | None = None
    scope_of_work: str | None = None
    experience_type: str | None = None


class ExperienceUpdate(BaseModel):
    project_name: str | None = Field(default=None, min_length=1, max_length=500)
    client_department: str | None = None
    authority_organization: str | None = None
    work_category: str | None = None
    subcategory: str | None = None
    location: str | None = None
    district: str | None = None
    state: str | None = None
    contract_value: Decimal | None = Field(default=None, ge=0)
    awarded_value: Decimal | None = Field(default=None, ge=0)
    completion_value: Decimal | None = Field(default=None, ge=0)
    start_date: date | None = None
    completion_date: date | None = None
    project_status: ProjectStatus | None = None
    description: str | None = None
    scope_of_work: str | None = None
    experience_type: str | None = None
    is_active: bool | None = None


class ExperiencePublic(ExperienceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MachineryCreate(BaseModel):
    equipment_name: str = Field(min_length=1, max_length=255)
    category: str | None = None
    quantity: int | None = Field(default=None, ge=0)
    ownership_type: OwnershipType = OwnershipType.OTHER
    registration_number: str | None = None
    capacity_specification: str | None = None
    available_from: date | None = None
    status: str | None = None
    notes: str | None = None


class MachineryUpdate(BaseModel):
    equipment_name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = None
    quantity: int | None = Field(default=None, ge=0)
    ownership_type: OwnershipType | None = None
    registration_number: str | None = None
    capacity_specification: str | None = None
    available_from: date | None = None
    status: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class MachineryPublic(MachineryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PersonnelCreate(BaseModel):
    designation: str = Field(min_length=1, max_length=150)
    qualification: str | None = None
    specialization: str | None = None
    experience_years: int | None = Field(default=None, ge=0)
    employment_type: str | None = None
    availability: str | None = None
    notes: str | None = None


class PersonnelUpdate(BaseModel):
    designation: str | None = Field(default=None, min_length=1, max_length=150)
    qualification: str | None = None
    specialization: str | None = None
    experience_years: int | None = Field(default=None, ge=0)
    employment_type: str | None = None
    availability: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class PersonnelPublic(PersonnelCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LocationCreate(BaseModel):
    state: str | None = None
    district: str | None = None
    region: str | None = None
    notes: str | None = None


class LocationPublic(LocationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DocumentTypePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None = None


class DocumentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    document_type: DocumentTypePublic
    related_entity_type: DocumentEntityType
    related_entity_id: UUID | None = None
    original_filename: str
    file_extension: str | None = None
    mime_type: str
    file_size: int
    document_status: DocumentStatus
    expiry_date: date | None = None
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str
