"""add announcements and audience tracking

Revision ID: f0a1b2c3d456
Revises: e8f1a2b3c456
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f0a1b2c3d456"
down_revision: str | Sequence[str] | None = "e8f1a2b3c456"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "announcements",
        sa.Column("announcement_code", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("author_id", sa.String(length=100), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_announcement_status",
        ),
        sa.CheckConstraint(
            "type IN ('general', 'maintenance', 'facility', 'regulation_update', 'event', 'emergency')",
            name="ck_announcement_type",
        ),
        sa.CheckConstraint(
            "priority IN ('normal', 'important', 'urgent')",
            name="ck_announcement_priority",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("announcement_code"),
    )
    op.create_index(op.f("ix_announcements_announcement_code"), "announcements", ["announcement_code"], unique=True)
    op.create_index(op.f("ix_announcements_author_id"), "announcements", ["author_id"], unique=False)
    op.create_index(op.f("ix_announcements_expires_at"), "announcements", ["expires_at"], unique=False)
    op.create_index(op.f("ix_announcements_priority"), "announcements", ["priority"], unique=False)
    op.create_index(op.f("ix_announcements_published_at"), "announcements", ["published_at"], unique=False)
    op.create_index(op.f("ix_announcements_status"), "announcements", ["status"], unique=False)
    op.create_index(op.f("ix_announcements_type"), "announcements", ["type"], unique=False)
    op.create_index("ix_announcement_status_published_at", "announcements", ["status", "published_at"], unique=False)
    op.create_index("ix_announcement_author_status", "announcements", ["author_id", "status"], unique=False)

    op.create_table(
        "announcement_scopes",
        sa.Column("scope_type", sa.String(length=20), nullable=False),
        sa.Column("project_code", sa.String(length=50), nullable=True),
        sa.Column("building", sa.String(length=100), nullable=True),
        sa.Column("unit_id", sa.String(length=36), nullable=True),
        sa.Column("announcement_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.CheckConstraint(
            "scope_type IN ('all_residents', 'project', 'building', 'unit')",
            name="ck_announcement_scope_type",
        ),
        sa.ForeignKeyConstraint(["announcement_id"], ["announcements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_announcement_scopes_announcement_id"), "announcement_scopes", ["announcement_id"])
    op.create_index(op.f("ix_announcement_scopes_building"), "announcement_scopes", ["building"])
    op.create_index(op.f("ix_announcement_scopes_project_code"), "announcement_scopes", ["project_code"])
    op.create_index(op.f("ix_announcement_scopes_unit_id"), "announcement_scopes", ["unit_id"])
    op.create_index(
        "ix_announcement_scope_announcement_type",
        "announcement_scopes",
        ["announcement_id", "scope_type"],
    )

    op.create_table(
        "announcement_reads",
        sa.Column("announcement_id", sa.String(length=36), nullable=False),
        sa.Column("resident_id", sa.String(length=36), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["announcement_id"], ["announcements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("announcement_id", "resident_id", name="uq_announcement_read_resident"),
    )
    op.create_index(op.f("ix_announcement_reads_announcement_id"), "announcement_reads", ["announcement_id"])
    op.create_index(op.f("ix_announcement_reads_resident_id"), "announcement_reads", ["resident_id"])
    op.create_index("ix_announcement_read_announcement", "announcement_reads", ["announcement_id", "read_at"])
    op.create_index("ix_announcement_read_resident", "announcement_reads", ["resident_id", "read_at"])

    op.create_table(
        "announcement_events",
        sa.Column("announcement_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("actor_type", sa.String(length=20), nullable=False),
        sa.Column("actor_id", sa.String(length=100), nullable=True),
        sa.Column("from_status", sa.String(length=20), nullable=True),
        sa.Column("to_status", sa.String(length=20), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.CheckConstraint(
            "actor_type IN ('anonymous', 'resident', 'management', 'system')",
            name="ck_announcement_event_actor_type",
        ),
        sa.ForeignKeyConstraint(["announcement_id"], ["announcements.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_announcement_events_announcement_id"), "announcement_events", ["announcement_id"])
    op.create_index(
        "ix_announcement_event_announcement_created",
        "announcement_events",
        ["announcement_id", "created_at"],
    )

    with op.batch_alter_table("ticket_attachments", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("announcement_id", sa.String(length=36), nullable=True))
        batch_op.create_index(op.f("ix_ticket_attachments_announcement_id"), ["announcement_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_ticket_attachments_announcement_id",
            "announcements",
            ["announcement_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("ticket_attachments", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_ticket_attachments_announcement_id", type_="foreignkey")
        batch_op.drop_index(op.f("ix_ticket_attachments_announcement_id"))
        batch_op.drop_column("announcement_id")

    op.drop_index("ix_announcement_event_announcement_created", table_name="announcement_events")
    op.drop_index(op.f("ix_announcement_events_announcement_id"), table_name="announcement_events")
    op.drop_table("announcement_events")

    op.drop_index("ix_announcement_read_resident", table_name="announcement_reads")
    op.drop_index("ix_announcement_read_announcement", table_name="announcement_reads")
    op.drop_index(op.f("ix_announcement_reads_resident_id"), table_name="announcement_reads")
    op.drop_index(op.f("ix_announcement_reads_announcement_id"), table_name="announcement_reads")
    op.drop_table("announcement_reads")

    op.drop_index("ix_announcement_scope_announcement_type", table_name="announcement_scopes")
    op.drop_index(op.f("ix_announcement_scopes_unit_id"), table_name="announcement_scopes")
    op.drop_index(op.f("ix_announcement_scopes_project_code"), table_name="announcement_scopes")
    op.drop_index(op.f("ix_announcement_scopes_building"), table_name="announcement_scopes")
    op.drop_index(op.f("ix_announcement_scopes_announcement_id"), table_name="announcement_scopes")
    op.drop_table("announcement_scopes")

    op.drop_index("ix_announcement_author_status", table_name="announcements")
    op.drop_index("ix_announcement_status_published_at", table_name="announcements")
    op.drop_index(op.f("ix_announcements_type"), table_name="announcements")
    op.drop_index(op.f("ix_announcements_status"), table_name="announcements")
    op.drop_index(op.f("ix_announcements_published_at"), table_name="announcements")
    op.drop_index(op.f("ix_announcements_priority"), table_name="announcements")
    op.drop_index(op.f("ix_announcements_expires_at"), table_name="announcements")
    op.drop_index(op.f("ix_announcements_author_id"), table_name="announcements")
    op.drop_index(op.f("ix_announcements_announcement_code"), table_name="announcements")
    op.drop_table("announcements")
