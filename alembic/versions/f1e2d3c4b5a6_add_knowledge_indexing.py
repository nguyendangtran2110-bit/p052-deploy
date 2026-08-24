"""add knowledge indexing state and hybrid retrieval metadata

Revision ID: f1e2d3c4b5a6
Revises: b1c2d3e4f567
Create Date: 2026-08-23 22:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f1e2d3c4b5a6"
down_revision: str | Sequence[str] | None = "b1c2d3e4f567"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    with op.batch_alter_table("knowledge_documents") as batch_op:
        batch_op.add_column(sa.Column("is_searchable", sa.Boolean(), server_default=sa.false(), nullable=False))
        batch_op.add_column(sa.Column("effective_to", sa.Date(), nullable=True))
        batch_op.create_index(
            "ix_knowledge_retrieval_visibility",
            ["status", "is_searchable", "effective_date", "effective_to"],
            unique=False,
        )

    with op.batch_alter_table("knowledge_chunks") as batch_op:
        batch_op.add_column(sa.Column("normalized_content", sa.Text(), server_default="", nullable=False))
        batch_op.add_column(sa.Column("line_start", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("line_end", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("char_start", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("char_end", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("embedding_model", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("embedding_version", sa.String(length=50), nullable=True))
        if not is_postgres:
            batch_op.add_column(sa.Column("search_vector", sa.Text(), nullable=True))

    if is_postgres:
        op.execute("ALTER TABLE knowledge_chunks ADD COLUMN search_vector tsvector")

    op.execute("UPDATE knowledge_chunks SET normalized_content = content WHERE normalized_content = ''")

    if is_postgres:
        op.execute(
            "UPDATE knowledge_chunks "
            "SET search_vector = to_tsvector('simple', COALESCE(normalized_content, ''))"
        )
        op.execute(
            "CREATE INDEX ix_knowledge_chunks_search_vector "
            "ON knowledge_chunks USING gin (search_vector)"
        )
    else:
        op.create_index("ix_knowledge_chunks_search_vector", "knowledge_chunks", ["search_vector"], unique=False)

    op.create_table(
        "knowledge_index_runs",
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("run_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=120), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("stats", sa.JSON(), nullable=False),
        sa.Column("requested_by", sa.String(length=120), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("run_type IN ('initial', 'reindex')", name="ck_knowledge_index_run_type"),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')",
            name="ck_knowledge_index_run_status",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_index_run_queue", "knowledge_index_runs", ["status", "next_attempt_at"], unique=False)
    op.create_index(
        "ix_knowledge_index_run_document_created",
        "knowledge_index_runs",
        ["document_id", "created_at"],
        unique=False,
    )
    op.create_index("ix_knowledge_index_runs_document_id", "knowledge_index_runs", ["document_id"], unique=False)
    if is_postgres:
        op.execute(
            "CREATE UNIQUE INDEX uq_knowledge_index_runs_active_document "
            "ON knowledge_index_runs (document_id) "
            "WHERE status IN ('queued', 'running')"
        )


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        op.execute("DROP INDEX IF EXISTS uq_knowledge_index_runs_active_document")
    op.drop_index("ix_knowledge_index_runs_document_id", table_name="knowledge_index_runs")
    op.drop_index("ix_knowledge_index_run_document_created", table_name="knowledge_index_runs")
    op.drop_index("ix_knowledge_index_run_queue", table_name="knowledge_index_runs")
    op.drop_table("knowledge_index_runs")

    if is_postgres:
        op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_search_vector")
    else:
        op.drop_index("ix_knowledge_chunks_search_vector", table_name="knowledge_chunks")
    with op.batch_alter_table("knowledge_chunks") as batch_op:
        batch_op.drop_column("search_vector")
        batch_op.drop_column("embedding_version")
        batch_op.drop_column("embedding_model")
        batch_op.drop_column("char_end")
        batch_op.drop_column("char_start")
        batch_op.drop_column("line_end")
        batch_op.drop_column("line_start")
        batch_op.drop_column("normalized_content")

    with op.batch_alter_table("knowledge_documents") as batch_op:
        batch_op.drop_index("ix_knowledge_retrieval_visibility")
        batch_op.drop_column("effective_to")
        batch_op.drop_column("is_searchable")
