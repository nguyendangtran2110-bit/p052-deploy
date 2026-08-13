"""add pending attachments and password reset tokens

Revision ID: e8f1a2b3c456
Revises: d7e9f0a1b234
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e8f1a2b3c456"
down_revision: str | Sequence[str] | None = "d7e9f0a1b234"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("ticket_attachments", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("uploader_id", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("message_id", sa.String(length=36), nullable=True))
        batch_op.alter_column(
            "ticket_id",
            existing_type=sa.String(length=36),
            nullable=True,
        )
        batch_op.create_index(op.f("ix_ticket_attachments_uploader_id"), ["uploader_id"], unique=False)
        batch_op.create_index(op.f("ix_ticket_attachments_message_id"), ["message_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_ticket_attachments_message_id",
            "messages",
            ["message_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(sa.text("UPDATE ticket_attachments SET uploader_id = 'legacy' WHERE uploader_id IS NULL"))

    with op.batch_alter_table("ticket_attachments") as batch_op:
        batch_op.alter_column(
            "uploader_id",
            existing_type=sa.String(length=100),
            nullable=False,
        )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["user_accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_password_reset_tokens_account_id"), "password_reset_tokens", ["account_id"])
    op.create_index(
        op.f("ix_password_reset_tokens_token_hash"),
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(op.f("ix_password_reset_tokens_used_at"), "password_reset_tokens", ["used_at"])
    op.create_index(
        "ix_password_reset_token_account_active",
        "password_reset_tokens",
        ["account_id", "used_at", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_password_reset_token_account_active", table_name="password_reset_tokens")
    op.drop_index(op.f("ix_password_reset_tokens_used_at"), table_name="password_reset_tokens")
    op.drop_index(op.f("ix_password_reset_tokens_token_hash"), table_name="password_reset_tokens")
    op.drop_index(op.f("ix_password_reset_tokens_account_id"), table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")

    with op.batch_alter_table("ticket_attachments", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_ticket_attachments_message_id", type_="foreignkey")
        batch_op.drop_index(op.f("ix_ticket_attachments_message_id"))
        batch_op.drop_index(op.f("ix_ticket_attachments_uploader_id"))
        batch_op.drop_column("message_id")
        batch_op.drop_column("uploader_id")
        batch_op.alter_column(
            "ticket_id",
            existing_type=sa.String(length=36),
            nullable=False,
        )
