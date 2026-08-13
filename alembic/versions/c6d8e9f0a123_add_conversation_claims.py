"""add conversation management claims

Revision ID: c6d8e9f0a123
Revises: b5c7d9e1f204
Create Date: 2026-08-10 16:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c6d8e9f0a123"
down_revision: str | Sequence[str] | None = "b5c7d9e1f204"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.add_column(sa.Column("claimed_by_id", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("claim_expires_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(
            sa.Column("claim_version", sa.Integer(), server_default="0", nullable=False)
        )
        batch_op.create_index(op.f("ix_conversations_claimed_by_id"), ["claimed_by_id"], unique=False)
        batch_op.create_index(op.f("ix_conversations_claim_expires_at"), ["claim_expires_at"], unique=False)
        batch_op.alter_column("claim_version", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.drop_index(op.f("ix_conversations_claim_expires_at"))
        batch_op.drop_index(op.f("ix_conversations_claimed_by_id"))
        batch_op.drop_column("claim_version")
        batch_op.drop_column("claim_expires_at")
        batch_op.drop_column("claimed_at")
        batch_op.drop_column("claimed_by_id")
