from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.infrastructure.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin

if TYPE_CHECKING:
    from src.backend.infrastructure.db.models.residents import Resident, Unit


class OnboardingChecklistTemplate(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "onboarding_checklist_templates"
    __table_args__ = (
        Index("ix_onboarding_template_scope", "project_code", "building", "unit_id", "is_active"),
    )

    template_code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    project_code: Mapped[str | None] = mapped_column(String(50), index=True)
    building: Mapped[str | None] = mapped_column(String(100), index=True)
    unit_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("units.id", ondelete="SET NULL"), index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    items: Mapped[list[OnboardingChecklistTemplateItem]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="OnboardingChecklistTemplateItem.sort_order",
    )
    resident_checklists: Mapped[list[ResidentOnboardingChecklist]] = relationship(back_populates="template")


class OnboardingChecklistTemplateItem(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "onboarding_checklist_template_items"
    __table_args__ = (
        UniqueConstraint("template_id", "code", name="uq_onboarding_template_item_code"),
        CheckConstraint(
            "category IN ('handover', 'utilities', 'guidance')",
            name="ck_onboarding_template_item_category",
        ),
        CheckConstraint(
            "item_type IN ('task', 'information')",
            name="ck_onboarding_template_item_type",
        ),
        Index("ix_onboarding_template_item_order", "template_id", "sort_order"),
    )

    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("onboarding_checklist_templates.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    handbook_reference: Mapped[str | None] = mapped_column(String(255))
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    template: Mapped[OnboardingChecklistTemplate] = relationship(back_populates="items")
    resident_items: Mapped[list[ResidentOnboardingItem]] = relationship(back_populates="template_item")


class ResidentOnboardingChecklist(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resident_onboarding_checklists"
    __table_args__ = (
        UniqueConstraint("resident_id", "unit_id", name="uq_resident_onboarding_checklist_unit"),
        Index("ix_resident_onboarding_checklist_resident", "resident_id", "updated_at"),
        Index("ix_resident_onboarding_checklist_unit", "unit_id", "updated_at"),
    )

    resident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("residents.id", ondelete="CASCADE"), index=True
    )
    unit_id: Mapped[str] = mapped_column(String(36), ForeignKey("units.id", ondelete="CASCADE"), index=True)
    template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("onboarding_checklist_templates.id", ondelete="SET NULL"), index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    resident: Mapped[Resident] = relationship(back_populates="onboarding_checklists")
    unit: Mapped[Unit] = relationship(back_populates="onboarding_checklists")
    template: Mapped[OnboardingChecklistTemplate | None] = relationship(back_populates="resident_checklists")
    items: Mapped[list[ResidentOnboardingItem]] = relationship(
        back_populates="checklist",
        cascade="all, delete-orphan",
        order_by="ResidentOnboardingItem.sort_order",
    )


class ResidentOnboardingItem(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resident_onboarding_items"
    __table_args__ = (
        UniqueConstraint("checklist_id", "code", name="uq_resident_onboarding_item_code"),
        CheckConstraint(
            "category IN ('handover', 'utilities', 'guidance')",
            name="ck_resident_onboarding_item_category",
        ),
        CheckConstraint(
            "item_type IN ('task', 'information')",
            name="ck_resident_onboarding_item_type",
        ),
        CheckConstraint(
            "status IN ('pending', 'completed', 'not_applicable', 'unread', 'read')",
            name="ck_resident_onboarding_item_status",
        ),
        Index("ix_resident_onboarding_item_checklist_status", "checklist_id", "status"),
    )

    checklist_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resident_onboarding_checklists.id", ondelete="CASCADE"), index=True
    )
    template_item_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("onboarding_checklist_template_items.id", ondelete="SET NULL"), index=True
    )
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    handbook_reference: Mapped[str | None] = mapped_column(String(255))
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    acted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    checklist: Mapped[ResidentOnboardingChecklist] = relationship(back_populates="items")
    template_item: Mapped[OnboardingChecklistTemplateItem | None] = relationship(back_populates="resident_items")
