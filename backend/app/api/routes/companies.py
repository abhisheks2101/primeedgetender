"""Company profile and document management routes."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response

from app.config import Settings
from app.core.deps import get_db, get_settings, require_company_read, require_company_write
from app.core.enums import DocumentEntityType
from app.models.user import User
from app.schemas.company import (
    CapabilityCategoryPublic,
    CompanyCapabilityAssign,
    CompanyCapabilityPublic,
    CompanyCreate,
    CompanyPublic,
    CompanySummary,
    CompanyUpdate,
    ContractorRegistrationCreate,
    ContractorRegistrationPublic,
    ContractorRegistrationUpdate,
    DocumentPublic,
    DocumentTypePublic,
    ExperienceCreate,
    ExperiencePublic,
    ExperienceUpdate,
    FinancialRecordCreate,
    FinancialRecordPublic,
    FinancialRecordUpdate,
    LocationCreate,
    LocationPublic,
    MachineryCreate,
    MachineryPublic,
    MachineryUpdate,
    MessageResponse,
    PersonnelCreate,
    PersonnelPublic,
    PersonnelUpdate,
    RegistrationCreate,
    RegistrationPublic,
    RegistrationUpdate,
)
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from sqlalchemy.orm import Session

router = APIRouter(prefix="/companies", tags=["companies"])


def get_company_service(db: Annotated[Session, Depends(get_db)]) -> CompanyService:
    return CompanyService(db)


def get_document_service(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentService:
    return DocumentService(db, settings)


@router.get("", response_model=list[CompanySummary])
def list_companies(
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
    search: str | None = Query(default=None),
    active_only: bool | None = Query(default=None),
) -> list[CompanySummary]:
    return service.list_companies(search=search, active_only=active_only)


@router.post("", response_model=CompanyPublic, status_code=status.HTTP_201_CREATED)
def create_company(
    payload: CompanyCreate,
    actor: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyPublic:
    return CompanyPublic.model_validate(service.create_company(payload, actor))


@router.get("/lookup/document-types", response_model=list[DocumentTypePublic])
def list_document_types(
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[DocumentTypePublic]:
    return [DocumentTypePublic.model_validate(item) for item in service.list_document_types()]


@router.get("/lookup/capability-categories", response_model=list[CapabilityCategoryPublic])
def list_capability_categories(
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[CapabilityCategoryPublic]:
    return [CapabilityCategoryPublic.model_validate(item) for item in service.list_capability_categories()]


@router.get("/{company_id}", response_model=CompanyPublic)
def get_company(
    company_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyPublic:
    return CompanyPublic.model_validate(service.get_company_or_404(company_id))


@router.patch("/{company_id}", response_model=CompanyPublic)
def update_company(
    company_id: UUID,
    payload: CompanyUpdate,
    actor: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyPublic:
    return CompanyPublic.model_validate(service.update_company(company_id, payload, actor))


@router.delete("/{company_id}", response_model=CompanyPublic)
def archive_company(
    company_id: UUID,
    actor: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyPublic:
    return CompanyPublic.model_validate(service.archive_company(company_id, actor))


@router.get("/{company_id}/registrations", response_model=list[RegistrationPublic])
def list_registrations(
    company_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[RegistrationPublic]:
    return [RegistrationPublic.model_validate(item) for item in service.list_registrations(company_id)]


@router.post("/{company_id}/registrations", response_model=RegistrationPublic, status_code=status.HTTP_201_CREATED)
def create_registration(
    company_id: UUID,
    payload: RegistrationCreate,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> RegistrationPublic:
    return RegistrationPublic.model_validate(service.create_registration(company_id, payload))


@router.patch("/{company_id}/registrations/{registration_id}", response_model=RegistrationPublic)
def update_registration(
    company_id: UUID,
    registration_id: UUID,
    payload: RegistrationUpdate,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> RegistrationPublic:
    return RegistrationPublic.model_validate(service.update_registration(company_id, registration_id, payload))


@router.delete("/{company_id}/registrations/{registration_id}", response_model=RegistrationPublic)
def archive_registration(
    company_id: UUID,
    registration_id: UUID,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> RegistrationPublic:
    return RegistrationPublic.model_validate(service.archive_registration(company_id, registration_id))


@router.get("/{company_id}/contractor-registrations", response_model=list[ContractorRegistrationPublic])
def list_contractor_registrations(
    company_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[ContractorRegistrationPublic]:
    return [ContractorRegistrationPublic.model_validate(item) for item in service.list_contractor_registrations(company_id)]


@router.post(
    "/{company_id}/contractor-registrations",
    response_model=ContractorRegistrationPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_contractor_registration(
    company_id: UUID,
    payload: ContractorRegistrationCreate,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> ContractorRegistrationPublic:
    return ContractorRegistrationPublic.model_validate(service.create_contractor_registration(company_id, payload))


@router.patch("/{company_id}/contractor-registrations/{item_id}", response_model=ContractorRegistrationPublic)
def update_contractor_registration(
    company_id: UUID,
    item_id: UUID,
    payload: ContractorRegistrationUpdate,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> ContractorRegistrationPublic:
    return ContractorRegistrationPublic.model_validate(service.update_contractor_registration(company_id, item_id, payload))


@router.delete("/{company_id}/contractor-registrations/{item_id}", response_model=ContractorRegistrationPublic)
def archive_contractor_registration(
    company_id: UUID,
    item_id: UUID,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> ContractorRegistrationPublic:
    return ContractorRegistrationPublic.model_validate(service.archive_contractor_registration(company_id, item_id))


@router.get("/{company_id}/financial-records", response_model=list[FinancialRecordPublic])
def list_financial_records(
    company_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[FinancialRecordPublic]:
    return [FinancialRecordPublic.model_validate(item) for item in service.list_financial_records(company_id)]


@router.post("/{company_id}/financial-records", response_model=FinancialRecordPublic, status_code=status.HTTP_201_CREATED)
def create_financial_record(
    company_id: UUID,
    payload: FinancialRecordCreate,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> FinancialRecordPublic:
    return FinancialRecordPublic.model_validate(service.create_financial_record(company_id, payload))


@router.patch("/{company_id}/financial-records/{item_id}", response_model=FinancialRecordPublic)
def update_financial_record(
    company_id: UUID,
    item_id: UUID,
    payload: FinancialRecordUpdate,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> FinancialRecordPublic:
    return FinancialRecordPublic.model_validate(service.update_financial_record(company_id, item_id, payload))


@router.delete("/{company_id}/financial-records/{item_id}", response_model=FinancialRecordPublic)
def archive_financial_record(
    company_id: UUID,
    item_id: UUID,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> FinancialRecordPublic:
    return FinancialRecordPublic.model_validate(service.archive_financial_record(company_id, item_id))


@router.get("/{company_id}/capabilities", response_model=list[CompanyCapabilityPublic])
def list_capabilities(
    company_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[CompanyCapabilityPublic]:
    return [CompanyCapabilityPublic.model_validate(item) for item in service.list_capabilities(company_id)]


@router.post("/{company_id}/capabilities", response_model=CompanyCapabilityPublic, status_code=status.HTTP_201_CREATED)
def assign_capability(
    company_id: UUID,
    payload: CompanyCapabilityAssign,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> CompanyCapabilityPublic:
    return CompanyCapabilityPublic.model_validate(service.assign_capability(company_id, payload))


@router.delete("/{company_id}/capabilities/{capability_link_id}", response_model=MessageResponse)
def unassign_capability(
    company_id: UUID,
    capability_link_id: UUID,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> MessageResponse:
    service.unassign_capability(company_id, capability_link_id)
    return MessageResponse(message="Capability unassigned.")


@router.get("/{company_id}/experiences", response_model=list[ExperiencePublic])
def list_experiences(
    company_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[ExperiencePublic]:
    return [ExperiencePublic.model_validate(item) for item in service.list_experiences(company_id)]


@router.post("/{company_id}/experiences", response_model=ExperiencePublic, status_code=status.HTTP_201_CREATED)
def create_experience(
    company_id: UUID,
    payload: ExperienceCreate,
    actor: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> ExperiencePublic:
    return ExperiencePublic.model_validate(service.create_experience(company_id, payload, actor))


@router.get("/{company_id}/experiences/{experience_id}", response_model=ExperiencePublic)
def get_experience(
    company_id: UUID,
    experience_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> ExperiencePublic:
    return ExperiencePublic.model_validate(service.get_experience(company_id, experience_id))


@router.patch("/{company_id}/experiences/{experience_id}", response_model=ExperiencePublic)
def update_experience(
    company_id: UUID,
    experience_id: UUID,
    payload: ExperienceUpdate,
    actor: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> ExperiencePublic:
    return ExperiencePublic.model_validate(service.update_experience(company_id, experience_id, payload, actor))


@router.delete("/{company_id}/experiences/{experience_id}", response_model=ExperiencePublic)
def archive_experience(
    company_id: UUID,
    experience_id: UUID,
    actor: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> ExperiencePublic:
    return ExperiencePublic.model_validate(service.archive_experience(company_id, experience_id, actor))


@router.get("/{company_id}/machinery", response_model=list[MachineryPublic])
def list_machinery(
    company_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[MachineryPublic]:
    return [MachineryPublic.model_validate(item) for item in service.list_machinery(company_id)]


@router.post("/{company_id}/machinery", response_model=MachineryPublic, status_code=status.HTTP_201_CREATED)
def create_machinery(
    company_id: UUID,
    payload: MachineryCreate,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> MachineryPublic:
    return MachineryPublic.model_validate(service.create_machinery(company_id, payload))


@router.patch("/{company_id}/machinery/{item_id}", response_model=MachineryPublic)
def update_machinery(
    company_id: UUID,
    item_id: UUID,
    payload: MachineryUpdate,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> MachineryPublic:
    return MachineryPublic.model_validate(service.update_machinery(company_id, item_id, payload))


@router.delete("/{company_id}/machinery/{item_id}", response_model=MachineryPublic)
def archive_machinery(
    company_id: UUID,
    item_id: UUID,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> MachineryPublic:
    return MachineryPublic.model_validate(service.archive_machinery(company_id, item_id))


@router.get("/{company_id}/personnel", response_model=list[PersonnelPublic])
def list_personnel(
    company_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[PersonnelPublic]:
    return [PersonnelPublic.model_validate(item) for item in service.list_personnel(company_id)]


@router.post("/{company_id}/personnel", response_model=PersonnelPublic, status_code=status.HTTP_201_CREATED)
def create_personnel(
    company_id: UUID,
    payload: PersonnelCreate,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> PersonnelPublic:
    return PersonnelPublic.model_validate(service.create_personnel(company_id, payload))


@router.patch("/{company_id}/personnel/{item_id}", response_model=PersonnelPublic)
def update_personnel(
    company_id: UUID,
    item_id: UUID,
    payload: PersonnelUpdate,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> PersonnelPublic:
    return PersonnelPublic.model_validate(service.update_personnel(company_id, item_id, payload))


@router.delete("/{company_id}/personnel/{item_id}", response_model=PersonnelPublic)
def archive_personnel(
    company_id: UUID,
    item_id: UUID,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> PersonnelPublic:
    return PersonnelPublic.model_validate(service.archive_personnel(company_id, item_id))


@router.get("/{company_id}/locations", response_model=list[LocationPublic])
def list_locations(
    company_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> list[LocationPublic]:
    return [LocationPublic.model_validate(item) for item in service.list_locations(company_id)]


@router.post("/{company_id}/locations", response_model=LocationPublic, status_code=status.HTTP_201_CREATED)
def create_location(
    company_id: UUID,
    payload: LocationCreate,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> LocationPublic:
    return LocationPublic.model_validate(service.create_location(company_id, payload))


@router.delete("/{company_id}/locations/{item_id}", response_model=MessageResponse)
def delete_location(
    company_id: UUID,
    item_id: UUID,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[CompanyService, Depends(get_company_service)],
) -> MessageResponse:
    service.delete_location(company_id, item_id)
    return MessageResponse(message="Location deleted.")


@router.get("/{company_id}/documents", response_model=list[DocumentPublic])
def list_documents(
    company_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> list[DocumentPublic]:
    return [DocumentPublic.model_validate(item) for item in service.list_documents(company_id)]


@router.post("/{company_id}/documents", response_model=DocumentPublic, status_code=status.HTTP_201_CREATED)
async def upload_document(
    company_id: UUID,
    actor: Annotated[User, Depends(require_company_write)],
    service: Annotated[DocumentService, Depends(get_document_service)],
    file: UploadFile = File(...),
    document_type_id: UUID = Form(...),
    related_entity_type: DocumentEntityType = Form(default=DocumentEntityType.COMPANY),
    related_entity_id: UUID | None = Form(default=None),
    expiry_date: date | None = Form(default=None),
    description: str | None = Form(default=None),
) -> DocumentPublic:
    return DocumentPublic.model_validate(
        await service.upload_document(
            company_id,
            file,
            document_type_id,
            related_entity_type,
            related_entity_id,
            expiry_date,
            description,
            actor,
        )
    )


documents_router = APIRouter(prefix="/documents", tags=["documents"])


@documents_router.get("/{document_id}", response_model=DocumentPublic)
def get_document_metadata(
    document_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentPublic:
    return DocumentPublic.model_validate(service.get_document(document_id))


@documents_router.get("/{document_id}/download")
def download_document(
    document_id: UUID,
    _: Annotated[User, Depends(require_company_read)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> Response:
    document, content = service.retrieve_document_content(document_id)
    return Response(
        content=content,
        media_type=document.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{document.original_filename}"'},
    )


@documents_router.delete("/{document_id}", response_model=DocumentPublic)
def archive_document(
    document_id: UUID,
    _: Annotated[User, Depends(require_company_write)],
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> DocumentPublic:
    return DocumentPublic.model_validate(service.archive_document(document_id))
