"""Migration: tender document processing support."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_document_processing"
down_revision: Union[str, None] = "006_normalization"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

classification_enum = postgresql.ENUM(
    "NIT", "BOQ", "TENDER_DOCUMENT", "TERMS_AND_CONDITIONS", "ELIGIBILITY_DOCUMENT",
    "DRAWING", "CORRIGENDUM", "ADDENDUM", "OTHER", "UNKNOWN",
    name="tender_document_classification", create_type=False,
)
download_status_enum = postgresql.ENUM(
    "DISCOVERED", "DOWNLOAD_QUEUED", "DOWNLOADING", "DOWNLOADED", "DOWNLOAD_FAILED", "ACCESS_RESTRICTED",
    name="tender_document_download_status", create_type=False,
)
processing_status_enum = postgresql.ENUM(
    "PENDING", "VALIDATED", "INVALID", "PROCESSING_FAILED", "UNSUPPORTED",
    name="tender_document_processing_status", create_type=False,
)
extraction_status_enum = postgresql.ENUM(
    "NOT_EXTRACTED", "TEXT_EXTRACTED", "OCR_REQUIRED", "OCR_COMPLETED", "EXTRACTION_FAILED",
    name="tender_document_extraction_status", create_type=False,
)
extraction_method_enum = postgresql.ENUM(
    "NONE", "DIRECT_EXTRACTION", "OCR",
    name="tender_document_extraction_method", create_type=False,
)
error_code_enum = postgresql.ENUM(
    "NETWORK_ERROR", "TIMEOUT", "HTTP_ERROR", "ACCESS_RESTRICTED", "INVALID_FILE",
    "UNSUPPORTED_FILE", "FILE_TOO_LARGE", "PARSE_ERROR", "OCR_ERROR", "STORAGE_ERROR", "UNKNOWN_ERROR",
    name="tender_document_error_code", create_type=False,
)
page_extraction_method_enum = postgresql.ENUM(
    "NONE", "DIRECT_EXTRACTION", "OCR",
    name="tender_document_page_extraction_method", create_type=False,
)
job_status_enum = postgresql.ENUM(
    "QUEUED", "RUNNING", "COMPLETED", "PARTIAL", "FAILED",
    name="tender_document_processing_job_status", create_type=False,
)
event_kind_enum = postgresql.ENUM(
    "DOCUMENT_DISCOVERED", "DOWNLOAD_STARTED", "DOWNLOAD_COMPLETED", "DOWNLOAD_FAILED",
    "FILE_VALIDATED", "FILE_REJECTED", "TEXT_EXTRACTION_STARTED", "TEXT_EXTRACTION_COMPLETED",
    "OCR_STARTED", "OCR_COMPLETED", "PROCESSING_COMPLETED", "PROCESSING_FAILED",
    name="tender_document_processing_event_kind", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    classification_enum.create(bind, checkfirst=True)
    download_status_enum.create(bind, checkfirst=True)
    processing_status_enum.create(bind, checkfirst=True)
    extraction_status_enum.create(bind, checkfirst=True)
    extraction_method_enum.create(bind, checkfirst=True)
    error_code_enum.create(bind, checkfirst=True)
    page_extraction_method_enum.create(bind, checkfirst=True)
    job_status_enum.create(bind, checkfirst=True)
    event_kind_enum.create(bind, checkfirst=True)

    op.add_column("tender_documents", sa.Column("source_document_id", sa.String(length=255), nullable=True))
    op.execute("UPDATE tender_documents SET source_document_id = COALESCE(source_reference, document_name, id::text)")
    op.alter_column("tender_documents", "source_document_id", nullable=False)

    op.add_column("tender_documents", sa.Column("classification", classification_enum, nullable=False, server_default="UNKNOWN"))
    op.add_column("tender_documents", sa.Column("local_storage_path", sa.String(length=1000), nullable=True))
    op.add_column("tender_documents", sa.Column("mime_type", sa.String(length=255), nullable=True))
    op.add_column("tender_documents", sa.Column("file_extension", sa.String(length=32), nullable=True))
    op.add_column("tender_documents", sa.Column("file_size", sa.Integer(), nullable=True))
    op.add_column("tender_documents", sa.Column("checksum", sa.String(length=64), nullable=True))
    op.add_column("tender_documents", sa.Column("previous_checksum", sa.String(length=64), nullable=True))
    op.add_column("tender_documents", sa.Column("download_status", download_status_enum, nullable=False, server_default="DISCOVERED"))
    op.add_column("tender_documents", sa.Column("processing_status", processing_status_enum, nullable=False, server_default="PENDING"))
    op.add_column("tender_documents", sa.Column("extraction_status", extraction_status_enum, nullable=False, server_default="NOT_EXTRACTED"))
    op.add_column("tender_documents", sa.Column("extraction_method", extraction_method_enum, nullable=False, server_default="NONE"))
    op.add_column("tender_documents", sa.Column("text_storage_path", sa.String(length=1000), nullable=True))
    op.add_column("tender_documents", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column("tender_documents", sa.Column("character_count", sa.Integer(), nullable=True))
    op.add_column("tender_documents", sa.Column("error_code", error_code_enum, nullable=True))
    op.add_column("tender_documents", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("tender_documents", sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tender_documents", sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tender_documents", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_unique_constraint("uq_tender_documents_source_document_id", "tender_documents", ["tender_id", "source_document_id"])
    op.create_index("ix_tender_documents_download_status", "tender_documents", ["download_status"])
    op.create_index("ix_tender_documents_processing_status", "tender_documents", ["processing_status"])
    op.create_index("ix_tender_documents_extraction_status", "tender_documents", ["extraction_status"])
    op.create_index("ix_tender_documents_checksum", "tender_documents", ["checksum"])

    op.create_table(
        "tender_document_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tender_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("extraction_method", page_extraction_method_enum, nullable=False, server_default="DIRECT_EXTRACTION"),
        sa.Column("character_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("document_id", "page_number", name="uq_tender_document_pages_page"),
    )
    op.create_index("ix_tender_document_pages_document_id", "tender_document_pages", ["document_id"])

    op.create_table(
        "tender_document_processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", job_status_enum, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("downloaded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("extracted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ocr_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tender_document_processing_jobs_tender_id", "tender_document_processing_jobs", ["tender_id"])

    op.create_table(
        "tender_document_processing_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tender_document_processing_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tender_documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", event_kind_enum, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tender_document_processing_events_job_id", "tender_document_processing_events", ["job_id"])


def downgrade() -> None:
    op.drop_table("tender_document_processing_events")
    op.drop_table("tender_document_processing_jobs")
    op.drop_table("tender_document_pages")
    op.drop_constraint("uq_tender_documents_source_document_id", "tender_documents", type_="unique")
    op.drop_index("ix_tender_documents_checksum", table_name="tender_documents")
    op.drop_index("ix_tender_documents_extraction_status", table_name="tender_documents")
    op.drop_index("ix_tender_documents_processing_status", table_name="tender_documents")
    op.drop_index("ix_tender_documents_download_status", table_name="tender_documents")
    for column in (
        "processed_at", "downloaded_at", "first_seen_at", "error_message", "error_code",
        "character_count", "page_count", "text_storage_path", "extraction_method", "extraction_status",
        "processing_status", "download_status", "previous_checksum", "checksum", "file_size",
        "file_extension", "mime_type", "local_storage_path", "classification", "source_document_id",
    ):
        op.drop_column("tender_documents", column)
    bind = op.get_bind()
    event_kind_enum.drop(bind, checkfirst=True)
    job_status_enum.drop(bind, checkfirst=True)
    page_extraction_method_enum.drop(bind, checkfirst=True)
    error_code_enum.drop(bind, checkfirst=True)
    extraction_method_enum.drop(bind, checkfirst=True)
    extraction_status_enum.drop(bind, checkfirst=True)
    processing_status_enum.drop(bind, checkfirst=True)
    download_status_enum.drop(bind, checkfirst=True)
    classification_enum.drop(bind, checkfirst=True)
