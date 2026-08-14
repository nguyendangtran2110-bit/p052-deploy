"""add AI workflow persistence and assistant conversation metadata

Revision ID: b7c8d9e0f123
Revises: a1b2c3d4e5f6
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b7c8d9e0f123"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.add_column(
            sa.Column("conversation_type", sa.String(length=30), server_default="resident_support", nullable=False)
        )
        batch_op.add_column(sa.Column("workflow_type", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("workflow_id", sa.String(length=36), nullable=True))
        batch_op.create_index(op.f("ix_conversations_conversation_type"), ["conversation_type"], unique=False)
        batch_op.create_index(op.f("ix_conversations_workflow_type"), ["workflow_type"], unique=False)
        batch_op.create_index(op.f("ix_conversations_workflow_id"), ["workflow_id"], unique=False)
        batch_op.create_check_constraint(
            "ck_conversation_type",
            "conversation_type IN ('resident_support', 'manager_assistant')",
        )
        batch_op.create_check_constraint(
            "ck_conversation_workflow_type",
            "workflow_type IS NULL OR workflow_type IN ('resident_ticket', 'manager_announcement')",
        )
        batch_op.alter_column("conversation_type", server_default=None)

    op.create_table(
        "ai_workflows",
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("workflow_type", sa.String(length=40), nullable=False),
        sa.Column("owner_actor_id", sa.String(length=100), nullable=False),
        sa.Column("owner_resident_id", sa.String(length=36), nullable=True),
        sa.Column("state", sa.String(length=40), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("draft", sa.JSON(), nullable=False),
        sa.Column("missing_fields", sa.JSON(), nullable=False),
        sa.Column("pending_action", sa.JSON(), nullable=True),
        sa.Column("attachment_ids", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("last_error", sa.JSON(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "workflow_type IN ('resident_ticket', 'manager_announcement')",
            name="ck_ai_workflow_type",
        ),
        sa.CheckConstraint(
            "state IN ('collecting', 'awaiting_confirmation', 'executing', 'completed', 'cancelled', 'failed', "
            "'awaiting_publish_confirmation', 'publishing', 'published')",
            name="ck_ai_workflow_state",
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_resident_id"], ["residents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id", name="uq_ai_workflow_conversation"),
    )
    op.create_index(op.f("ix_ai_workflows_conversation_id"), "ai_workflows", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_ai_workflows_owner_actor_id"), "ai_workflows", ["owner_actor_id"], unique=False)
    op.create_index(op.f("ix_ai_workflows_owner_resident_id"), "ai_workflows", ["owner_resident_id"], unique=False)
    op.create_index(op.f("ix_ai_workflows_state"), "ai_workflows", ["state"], unique=False)
    op.create_index("ix_ai_workflow_conversation_updated", "ai_workflows", ["conversation_id", "updated_at"], unique=False)
    op.create_index("ix_ai_workflow_owner_state", "ai_workflows", ["owner_actor_id", "state"], unique=False)

    with op.batch_alter_table("messages") as batch_op:
        batch_op.add_column(sa.Column("workflow_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("workflow_state", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("workflow_version", sa.Integer(), nullable=True))
        batch_op.create_index(op.f("ix_messages_workflow_id"), ["workflow_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_messages_workflow_id",
            "ai_workflows",
            ["workflow_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("ticket_attachments") as batch_op:
        batch_op.add_column(sa.Column("workflow_id", sa.String(length=36), nullable=True))
        batch_op.create_index(op.f("ix_ticket_attachments_workflow_id"), ["workflow_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_ticket_attachments_workflow_id",
            "ai_workflows",
            ["workflow_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.create_table(
        "ai_workflow_actions",
        sa.Column("workflow_id", sa.String(length=36), nullable=False),
        sa.Column("action_id", sa.String(length=36), nullable=False),
        sa.Column("action_type", sa.String(length=60), nullable=False),
        sa.Column("workflow_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("error_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'executing', 'succeeded', 'failed', 'unknown', 'cancelled')",
            name="ck_ai_workflow_action_status",
        ),
        sa.ForeignKeyConstraint(["workflow_id"], ["ai_workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_id", "action_id", name="uq_ai_workflow_action_id"),
    )
    op.create_index(op.f("ix_ai_workflow_actions_workflow_id"), "ai_workflow_actions", ["workflow_id"], unique=False)
    op.create_index(
        "ix_ai_workflow_action_workflow_created",
        "ai_workflow_actions",
        ["workflow_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    with op.batch_alter_table("messages") as batch_op:
        batch_op.drop_constraint("fk_messages_workflow_id", type_="foreignkey")
        batch_op.drop_index(op.f("ix_messages_workflow_id"))
        batch_op.drop_column("workflow_version")
        batch_op.drop_column("workflow_state")
        batch_op.drop_column("workflow_id")

    with op.batch_alter_table("ticket_attachments") as batch_op:
        batch_op.drop_constraint("fk_ticket_attachments_workflow_id", type_="foreignkey")
        batch_op.drop_index(op.f("ix_ticket_attachments_workflow_id"))
        batch_op.drop_column("workflow_id")

    op.drop_index("ix_ai_workflow_action_workflow_created", table_name="ai_workflow_actions")
    op.drop_index(op.f("ix_ai_workflow_actions_workflow_id"), table_name="ai_workflow_actions")
    op.drop_table("ai_workflow_actions")
    op.drop_index("ix_ai_workflow_owner_state", table_name="ai_workflows")
    op.drop_index("ix_ai_workflow_conversation_updated", table_name="ai_workflows")
    op.drop_index(op.f("ix_ai_workflows_state"), table_name="ai_workflows")
    op.drop_index(op.f("ix_ai_workflows_owner_resident_id"), table_name="ai_workflows")
    op.drop_index(op.f("ix_ai_workflows_owner_actor_id"), table_name="ai_workflows")
    op.drop_index(op.f("ix_ai_workflows_conversation_id"), table_name="ai_workflows")
    op.drop_table("ai_workflows")

    with op.batch_alter_table("conversations") as batch_op:
        batch_op.drop_constraint("ck_conversation_workflow_type", type_="check")
        batch_op.drop_constraint("ck_conversation_type", type_="check")
        batch_op.drop_index(op.f("ix_conversations_workflow_id"))
        batch_op.drop_index(op.f("ix_conversations_workflow_type"))
        batch_op.drop_index(op.f("ix_conversations_conversation_type"))
        batch_op.drop_column("workflow_id")
        batch_op.drop_column("workflow_type")
        batch_op.drop_column("conversation_type")
