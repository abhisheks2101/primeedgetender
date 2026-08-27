"""Company document upload and retrieval."""

from datetime import date
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import Settings
from app.core.document_utils import (
    compute_document_status,
    detect_mime_type,
    generate_stored_filename,
    sanitize_filename,
    validate_upload_file,
)
from app.core.enums import DocumentEntityType
from app.models.company import CompanyDocument, DocumentType
from app.models.user import User
from app.services.company_service import CompanyService
from app.services.storage.local_storage import LocalStorageService


class DocumentService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.storage = LocalStorageService(settings)
        self.company_service = CompanyService(db)

    def list_documents(self, company_id: UUID) -> list[CompanyDocument]:
        self.company_service.get_company_or_404(company_id)
        return self.db.scalars(
            select(CompanyDocument)
            .options(selectinload(CompanyDocument.document_type))
            .where(CompanyDocument.company_id == company_id, CompanyDocument.is_active.is_(True))
            .order_by(CompanyDocument.created_at.desc())
        ).all()

    def get_document(self, document_id: UUID) -> CompanyDocument:
        document = self.db.scalar(
            select(CompanyDocument)
            .options(selectinload(CompanyDocument.document_type))
            .where(CompanyDocument.id == document_id, CompanyDocument.is_active.is_(True))
        )
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
        return document

    async def upload_document(
        self,
        company_id: UUID,
        upload: UploadFile,
        document_type_id: UUID,
        related_entity_type: DocumentEntityType,
        related_entity_id: UUID | None,
        expiry_date: date | None,
        description: str | None,
        actor: User,
    ) -> CompanyDocument:
        self.company_service.get_company_or_404(company_id)
        document_type = self.db.get(DocumentType, document_type_id)
        if document_type is None or not document_type.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document type not found.")

        original_filename = sanitize_filename(upload.filename or "upload.bin")
        content = await upload.read()
        mime_type = upload.content_type or detect_mime_type(original_filename)
        try:
            validate_upload_file(
                original_filename,
                mime_type,
                len(content),
                self.settings.allowed_mime_types,
                self.settings.max_upload_size_bytes,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        stored_filename = generate_stored_filename(original_filename)
        stored = self.storage.store(str(company_id), stored_filename, content)
        document = CompanyDocument(
            company_id=company_id,
            document_type_id=document_type_id,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            original_filename=original_filename,
            stored_filename=stored.stored_filename,
            file_extension=original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else None,
            mime_type=mime_type,
            file_size=len(content),
            storage_path=stored.storage_path,
            uploaded_by=actor.id,
            expiry_date=expiry_date,
            description=description,
            document_status=compute_document_status(expiry_date, self.settings.document_expiring_soon_days),
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return self.get_document(document.id)

    def retrieve_document_content(self, document_id: UUID) -> tuple[CompanyDocument, bytes]:
        document = self.get_document(document_id)
        if not self.storage.exists(document.storage_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found.")
        return document, self.storage.retrieve(document.storage_path)

    def archive_document(self, document_id: UUID) -> CompanyDocument:
        document = self.get_document(document_id)
        document.is_active = False
        self.db.commit()
        self.db.refresh(document)
        return document
