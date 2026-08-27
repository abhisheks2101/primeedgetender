"""Create normalized tender tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_tenders"
down_revision: Union[str, None] = "004_tender_sources"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

tender_status_enum = postgresql.ENUM(
    "OPEN", "CLOSED", "CANCELLED", "AWARDED", "UNKNOWN", name="tender_status", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    tender_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "tenders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tender_source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tender_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_tender_id", sa.String(length=255), nullable=False),
        sa.Column("reference_number", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=1000), nullable=True),
        sa.Column("work_description", sa.Text(), nullable=True),
        sa.Column("organization", sa.String(length=500), nullable=True),
        sa.Column("department", sa.String(length=500), nullable=True),
        sa.Column("tender_type", sa.String(length=120), nullable=True),
        sa.Column("tender_category", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("district", sa.String(length=255), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("estimated_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("emd_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("tender_fee", sa.Numeric(18, 2), nullable=True),
        sa.Column("publication_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("document_sale_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("document_sale_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submission_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submission_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opening_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", tender_status_enum, nullable=False, server_default="UNKNOWN"),
        sa.Column("source_status", sa.String(length=255), nullable=True),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("payload_hash", sa.String(length=64), nullable=True),
        sa.Column("source_last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tender_source_id", "source_tender_id", name="uq_tenders_source_tender_id"),
    )
    op.create_index("ix_tenders_source_id", "tenders", ["tender_source_id"])
    op.create_index("ix_tenders_status", "tenders", ["status"])
    op.create_index("ix_tenders_reference_number", "tenders", ["reference_number"])
    op.create_index("ix_tenders_submission_end", "tenders", ["submission_end"])

    op.create_table(
        "tender_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_name", sa.String(length=500), nullable=False),
        sa.Column("document_url", sa.String(length=1000), nullable=True),
        sa.Column("document_type", sa.String(length=255), nullable=True),
        sa.Column("source_reference", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tender_documents_tender_id", "tender_documents", ["tender_id"])


def downgrade() -> None:
    op.drop_table("tender_documents")
    op.drop_table("tenders")
    bind = op.get_bind()
    tender_status_enum.drop(bind, checkfirst=True)
