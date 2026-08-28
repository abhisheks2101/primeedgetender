"""Add normalization and deduplication support."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_normalization"
down_revision: Union[str, None] = "005_tenders"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

indian_state_enum = postgresql.ENUM(
    "UTTAR_PRADESH", "MADHYA_PRADESH", "UNKNOWN", name="indian_state_code", create_type=False
)
normalization_status_enum = postgresql.ENUM(
    "NOT_PROCESSED", "NORMALIZED", "FAILED", "NEEDS_REVIEW", name="normalization_status", create_type=False
)
duplicate_match_enum = postgresql.ENUM(
    "EXACT_DUPLICATE", "LIKELY_DUPLICATE", "POSSIBLE_DUPLICATE", "NOT_DUPLICATE",
    name="duplicate_match_type", create_type=False,
)
duplicate_review_enum = postgresql.ENUM(
    "PENDING", "CONFIRMED_DUPLICATE", "NOT_DUPLICATE", "IGNORED",
    name="duplicate_review_status", create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    indian_state_enum.create(bind, checkfirst=True)
    normalization_status_enum.create(bind, checkfirst=True)
    duplicate_match_enum.create(bind, checkfirst=True)
    duplicate_review_enum.create(bind, checkfirst=True)

    op.add_column("tenders", sa.Column("state_code", indian_state_enum, nullable=False, server_default="UNKNOWN"))
    op.add_column("tenders", sa.Column("original_location_text", sa.String(length=500), nullable=True))
    op.add_column("tenders", sa.Column("title_normalized", sa.String(length=1000), nullable=True))
    op.add_column("tenders", sa.Column("description_normalized", sa.Text(), nullable=True))
    op.add_column("tenders", sa.Column("organization_normalized", sa.String(length=500), nullable=True))
    op.add_column("tenders", sa.Column("normalization_version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("tenders", sa.Column("normalization_status", normalization_status_enum, nullable=False, server_default="NOT_PROCESSED"))
    op.add_column("tenders", sa.Column("validation_warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("tenders", sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tenders", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tenders", sa.Column("normalized_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_tenders_state_code", "tenders", ["state_code"])
    op.create_index("ix_tenders_organization", "tenders", ["organization"])
    op.create_index("ix_tenders_department", "tenders", ["department"])
    op.create_index("ix_tenders_normalization_status", "tenders", ["normalization_status"])

    op.create_table(
        "tender_change_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_name", sa.String(length=120), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tender_change_history_tender_id", "tender_change_history", ["tender_id"])

    op.create_table(
        "tender_duplicate_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("candidate_tender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_type", duplicate_match_enum, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("matched_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("review_status", duplicate_review_enum, nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tender_id", "candidate_tender_id", name="uq_tender_duplicate_pair"),
    )
    op.create_index("ix_tender_duplicate_candidates_status", "tender_duplicate_candidates", ["review_status"])
    op.create_index("ix_tender_duplicate_candidates_match_type", "tender_duplicate_candidates", ["match_type"])


def downgrade() -> None:
    op.drop_table("tender_duplicate_candidates")
    op.drop_table("tender_change_history")
    op.drop_index("ix_tenders_normalization_status", table_name="tenders")
    op.drop_index("ix_tenders_department", table_name="tenders")
    op.drop_index("ix_tenders_organization", table_name="tenders")
    op.drop_index("ix_tenders_state_code", table_name="tenders")
    for column in (
        "normalized_at", "last_seen_at", "first_seen_at", "validation_warnings", "normalization_status",
        "normalization_version", "organization_normalized", "description_normalized", "title_normalized",
        "original_location_text", "state_code",
    ):
        op.drop_column("tenders", column)
    bind = op.get_bind()
    duplicate_review_enum.drop(bind, checkfirst=True)
    duplicate_match_enum.drop(bind, checkfirst=True)
    normalization_status_enum.drop(bind, checkfirst=True)
    indian_state_enum.drop(bind, checkfirst=True)
