"""add resident onboarding checklists

Revision ID: a9b8c7d6e5f4
Revises: f0a1b2c3d456
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a9b8c7d6e5f4"
down_revision: str | Sequence[str] | None = "f0a1b2c3d456"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "onboarding_checklist_templates",
        sa.Column("template_code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("project_code", sa.String(length=50), nullable=True),
        sa.Column("building", sa.String(length=100), nullable=True),
        sa.Column("unit_id", sa.String(length=36), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_code"),
    )
    op.create_index(
        op.f("ix_onboarding_checklist_templates_template_code"),
        "onboarding_checklist_templates",
        ["template_code"],
        unique=True,
    )
    op.create_index(
        op.f("ix_onboarding_checklist_templates_project_code"),
        "onboarding_checklist_templates",
        ["project_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_onboarding_checklist_templates_building"),
        "onboarding_checklist_templates",
        ["building"],
        unique=False,
    )
    op.create_index(
        op.f("ix_onboarding_checklist_templates_unit_id"),
        "onboarding_checklist_templates",
        ["unit_id"],
        unique=False,
    )
    op.create_index(
        "ix_onboarding_template_scope",
        "onboarding_checklist_templates",
        ["project_code", "building", "unit_id", "is_active"],
        unique=False,
    )

    op.create_table(
        "onboarding_checklist_template_items",
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("handbook_reference", sa.String(length=255), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "category IN ('handover', 'utilities', 'guidance')",
            name="ck_onboarding_template_item_category",
        ),
        sa.CheckConstraint(
            "item_type IN ('task', 'information')",
            name="ck_onboarding_template_item_type",
        ),
        sa.ForeignKeyConstraint(["template_id"], ["onboarding_checklist_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "code", name="uq_onboarding_template_item_code"),
    )
    op.create_index(
        op.f("ix_onboarding_checklist_template_items_template_id"),
        "onboarding_checklist_template_items",
        ["template_id"],
        unique=False,
    )
    op.create_index(
        "ix_onboarding_template_item_order",
        "onboarding_checklist_template_items",
        ["template_id", "sort_order"],
        unique=False,
    )

    op.create_table(
        "resident_onboarding_checklists",
        sa.Column("resident_id", sa.String(length=36), nullable=False),
        sa.Column("unit_id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["template_id"], ["onboarding_checklist_templates.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resident_id", "unit_id", name="uq_resident_onboarding_checklist_unit"),
    )
    op.create_index(
        op.f("ix_resident_onboarding_checklists_resident_id"),
        "resident_onboarding_checklists",
        ["resident_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_resident_onboarding_checklists_unit_id"),
        "resident_onboarding_checklists",
        ["unit_id"],
        unique=False,
    )
    op.create_index(
        "ix_resident_onboarding_checklist_resident",
        "resident_onboarding_checklists",
        ["resident_id", "updated_at"],
        unique=False,
    )
    op.create_index(
        "ix_resident_onboarding_checklist_unit",
        "resident_onboarding_checklists",
        ["unit_id", "updated_at"],
        unique=False,
    )

    op.create_table(
        "resident_onboarding_items",
        sa.Column("checklist_id", sa.String(length=36), nullable=False),
        sa.Column("template_item_id", sa.String(length=36), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("item_type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("handbook_reference", sa.String(length=255), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "category IN ('handover', 'utilities', 'guidance')",
            name="ck_resident_onboarding_item_category",
        ),
        sa.CheckConstraint(
            "item_type IN ('task', 'information')",
            name="ck_resident_onboarding_item_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'not_applicable', 'unread', 'read')",
            name="ck_resident_onboarding_item_status",
        ),
        sa.ForeignKeyConstraint(
            ["checklist_id"], ["resident_onboarding_checklists.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["template_item_id"], ["onboarding_checklist_template_items.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("checklist_id", "code", name="uq_resident_onboarding_item_code"),
    )
    op.create_index(
        op.f("ix_resident_onboarding_items_checklist_id"),
        "resident_onboarding_items",
        ["checklist_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_resident_onboarding_items_template_item_id"),
        "resident_onboarding_items",
        ["template_item_id"],
        unique=False,
    )
    op.create_index(
        "ix_resident_onboarding_item_checklist_status",
        "resident_onboarding_items",
        ["checklist_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_resident_onboarding_item_checklist_status", table_name="resident_onboarding_items")
    op.drop_index(op.f("ix_resident_onboarding_items_template_item_id"), table_name="resident_onboarding_items")
    op.drop_index(op.f("ix_resident_onboarding_items_checklist_id"), table_name="resident_onboarding_items")
    op.drop_table("resident_onboarding_items")

    op.drop_index("ix_resident_onboarding_checklist_unit", table_name="resident_onboarding_checklists")
    op.drop_index("ix_resident_onboarding_checklist_resident", table_name="resident_onboarding_checklists")
    op.drop_index(op.f("ix_resident_onboarding_checklists_unit_id"), table_name="resident_onboarding_checklists")
    op.drop_index(op.f("ix_resident_onboarding_checklists_resident_id"), table_name="resident_onboarding_checklists")
    op.drop_table("resident_onboarding_checklists")

    op.drop_index("ix_onboarding_template_item_order", table_name="onboarding_checklist_template_items")
    op.drop_index(
        op.f("ix_onboarding_checklist_template_items_template_id"),
        table_name="onboarding_checklist_template_items",
    )
    op.drop_table("onboarding_checklist_template_items")

    op.drop_index("ix_onboarding_template_scope", table_name="onboarding_checklist_templates")
    op.drop_index(op.f("ix_onboarding_checklist_templates_unit_id"), table_name="onboarding_checklist_templates")
    op.drop_index(op.f("ix_onboarding_checklist_templates_building"), table_name="onboarding_checklist_templates")
    op.drop_index(
        op.f("ix_onboarding_checklist_templates_project_code"),
        table_name="onboarding_checklist_templates",
    )
    op.drop_index(
        op.f("ix_onboarding_checklist_templates_template_code"),
        table_name="onboarding_checklist_templates",
    )
    op.drop_table("onboarding_checklist_templates")
