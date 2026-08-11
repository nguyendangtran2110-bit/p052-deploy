"""add email verification tokens

Revision ID: a1b2c3d4e5f6
Revises: f0a1b2c3d456
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f0a1b2c3d456"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user_accounts", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.execute(sa.text("UPDATE user_accounts SET email_verified_at = created_at WHERE email_verified_at IS NULL"))
    op.create_table(
        "email_verification_tokens",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("request_ip", sa.String(length=64), nullable=True),
        sa.Column("resident_id", sa.String(length=36), nullable=False),
        sa.Column("resident_code", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=500), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_email_verification_tokens_email", "email_verification_tokens", ["email"], unique=False)
    op.create_index("ix_email_verification_tokens_request_ip", "email_verification_tokens", ["request_ip"], unique=False)
    op.create_index(
        "ix_email_verification_tokens_resident_id", "email_verification_tokens", ["resident_id"], unique=False
    )
    op.create_index(
        "ix_email_verification_tokens_token_hash", "email_verification_tokens", ["token_hash"], unique=True
    )
    op.create_index(
        "ix_email_verification_tokens_expires_at", "email_verification_tokens", ["expires_at"], unique=False
    )
    op.create_index(
        "ix_email_verification_tokens_used_at", "email_verification_tokens", ["used_at"], unique=False
    )
    op.create_index(
        "ix_email_verification_email_active",
        "email_verification_tokens",
        ["email", "used_at", "expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_email_verification_email_active", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_used_at", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_expires_at", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_token_hash", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_request_ip", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_resident_id", table_name="email_verification_tokens")
    op.drop_index("ix_email_verification_tokens_email", table_name="email_verification_tokens")
    op.drop_table("email_verification_tokens")
    op.drop_column("user_accounts", "email_verified_at")
