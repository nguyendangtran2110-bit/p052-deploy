from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.domain.residents.enums import ResidentUnitRole
from src.backend.infrastructure.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from src.backend.infrastructure.db.models.conversations import Conversation
    from src.backend.infrastructure.db.models.identity import UserAccount
    from src.backend.infrastructure.db.models.onboarding import ResidentOnboardingChecklist
    from src.backend.infrastructure.db.models.tickets import Ticket


class Resident(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "residents"

    resident_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(30), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    account: Mapped[UserAccount | None] = relationship(back_populates="resident", uselist=False)
    unit_links: Mapped[list[ResidentUnit]] = relationship(back_populates="resident", cascade="all, delete-orphan")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="resident")
    tickets: Mapped[list[Ticket]] = relationship(back_populates="resident")
    onboarding_checklists: Mapped[list[ResidentOnboardingChecklist]] = relationship(
        back_populates="resident", cascade="all, delete-orphan"
    )


class Unit(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("project_code", "building", "unit_number", name="uq_unit_location"),)

    project_code: Mapped[str] = mapped_column(String(50), index=True)
    building: Mapped[str] = mapped_column(String(100), index=True)
    floor: Mapped[str | None] = mapped_column(String(20))
    unit_number: Mapped[str] = mapped_column(String(50), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    resident_links: Mapped[list[ResidentUnit]] = relationship(back_populates="unit", cascade="all, delete-orphan")
    conversations: Mapped[list[Conversation]] = relationship(back_populates="unit")
    tickets: Mapped[list[Ticket]] = relationship(back_populates="unit")
    onboarding_checklists: Mapped[list[ResidentOnboardingChecklist]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )


class ResidentUnit(Base):
    __tablename__ = "resident_units"
    __table_args__ = (CheckConstraint("role IN ('owner', 'tenant', 'family')", name="ck_resident_unit_role"),)

    resident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("residents.id", ondelete="CASCADE"), primary_key=True
    )
    unit_id: Mapped[str] = mapped_column(String(36), ForeignKey("units.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), default=ResidentUnitRole.OWNER.value, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active_from: Mapped[date | None] = mapped_column(Date)
    active_to: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    resident: Mapped[Resident] = relationship(back_populates="unit_links")
    unit: Mapped[Unit] = relationship(back_populates="resident_links")
