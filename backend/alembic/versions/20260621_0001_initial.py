"""Create documents, citizen profiles, and analyses.

Revision ID: 20260621_0001
Revises: None
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260621_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("extracted_fields", sa.JSON(), nullable=False),
        sa.Column("extractor", sa.String(length=50), nullable=False),
        sa.Column("extraction_status", sa.String(length=30), nullable=False),
        sa.Column("extraction_failure_reason", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_document_type", "documents", ["document_type"])
    op.create_table(
        "citizen_profiles",
        sa.Column("fields", sa.JSON(), nullable=False),
        sa.Column("conflicts", sa.JSON(), nullable=False),
        sa.Column("missing_fields", sa.JSON(), nullable=False),
        sa.Column("document_ids", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "analyses",
        sa.Column("citizen_profile_id", sa.String(length=36), nullable=False),
        sa.Column("program_id", sa.String(length=100), nullable=False),
        sa.Column("eligible", sa.Boolean(), nullable=True),
        sa.Column("readiness_score", sa.Float(), nullable=True),
        sa.Column("risk_level", sa.String(length=20), nullable=True),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["citizen_profile_id"], ["citizen_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analyses_citizen_profile_id", "analyses", ["citizen_profile_id"])
    op.create_index("ix_analyses_program_id", "analyses", ["program_id"])


def downgrade() -> None:
    op.drop_index("ix_analyses_program_id", table_name="analyses")
    op.drop_index("ix_analyses_citizen_profile_id", table_name="analyses")
    op.drop_table("analyses")
    op.drop_table("citizen_profiles")
    op.drop_index("ix_documents_document_type", table_name="documents")
    op.drop_table("documents")

