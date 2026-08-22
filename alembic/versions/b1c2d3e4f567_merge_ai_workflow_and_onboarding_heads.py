"""merge AI workflow and onboarding migration heads

Revision ID: b1c2d3e4f567
Revises: a9b8c7d6e5f4, b7c8d9e0f123
"""

from collections.abc import Sequence

revision: str = "b1c2d3e4f567"
down_revision: tuple[str, str] = ("a9b8c7d6e5f4", "b7c8d9e0f123")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
