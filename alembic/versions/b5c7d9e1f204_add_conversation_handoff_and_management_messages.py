"""add conversation handoff and management message authors

Revision ID: b5c7d9e1f204
Revises: 7f4a1c2d9b3e
Create Date: 2026-08-10 13:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b5c7d9e1f204"
down_revision: str | Sequence[str] | None = "7f4a1c2d9b3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.add_column(
            sa.Column(
                "handoff_status",
                sa.String(length=30),
                server_default="bot_active",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("handoff_requested_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_check_constraint(
            "ck_conversation_handoff_status",
            "handoff_status IN ('bot_active', 'waiting_management', 'management_active')",
        )
        batch_op.create_index(op.f("ix_conversations_handoff_status"), ["handoff_status"], unique=False)
        batch_op.alter_column("handoff_status", server_default=None)

    with op.batch_alter_table("messages") as batch_op:
        batch_op.add_column(sa.Column("author_id", sa.String(length=100), nullable=True))
        batch_op.drop_constraint("ck_message_role", type_="check")
        batch_op.create_check_constraint(
            "ck_message_role",
            "role IN ('user', 'assistant', 'management', 'system')",
        )
        batch_op.create_index(op.f("ix_messages_author_id"), ["author_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("messages") as batch_op:
        batch_op.drop_index(op.f("ix_messages_author_id"))
        batch_op.drop_constraint("ck_message_role", type_="check")
        batch_op.create_check_constraint(
            "ck_message_role",
            "role IN ('user', 'assistant', 'system')",
        )
        batch_op.drop_column("author_id")

    with op.batch_alter_table("conversations") as batch_op:
        batch_op.drop_index(op.f("ix_conversations_handoff_status"))
        batch_op.drop_constraint("ck_conversation_handoff_status", type_="check")
        batch_op.drop_column("handoff_requested_at")
        batch_op.drop_column("handoff_status")
