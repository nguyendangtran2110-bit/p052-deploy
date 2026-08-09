from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.domain.identity.enums import AccountStatus, ManagementRole
from src.backend.infrastructure.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from src.backend.infrastructure.db.models.residents import Resident


class UserAccount(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_accounts"
    __table_args__ = (
        CheckConstraint("role IN ('resident', 'management')", name="ck_user_account_role"),
        CheckConstraint("status IN ('active', 'disabled')", name="ck_user_account_status"),
    )

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(500))
    role: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20), default=AccountStatus.ACTIVE.value, index=True, nullable=False)
    resident_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("residents.id", ondelete="SET NULL"), unique=True, index=True
    )
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    resident: Mapped[Resident | None] = relationship(back_populates="account")
    management_profile: Mapped[ManagementProfile | None] = relationship(
        back_populates="account", cascade="all, delete-orphan", uselist=False
    )
    refresh_sessions: Mapped[list[RefreshSession]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )


class ManagementProfile(TimestampMixin, Base):
    __tablename__ = "management_profiles"
    __table_args__ = (
        CheckConstraint(
            "management_role IN ('admin', 'manager', 'staff')",
            name="ck_management_profile_role",
        ),
    )

    account_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), primary_key=True
    )
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(30), unique=True)
    department: Mapped[str | None] = mapped_column(String(100), index=True)
    job_title: Mapped[str | None] = mapped_column(String(100))
    management_role: Mapped[str] = mapped_column(
        String(20), default=ManagementRole.STAFF.value, index=True, nullable=False
    )
    project_code: Mapped[str | None] = mapped_column(String(50), index=True)
    building: Mapped[str | None] = mapped_column(String(100), index=True)

    account: Mapped[UserAccount] = relationship(back_populates="management_profile")


class RefreshSession(UuidPrimaryKeyMixin, Base):
    __tablename__ = "refresh_sessions"
    __table_args__ = (Index("ix_refresh_session_account_active", "account_id", "revoked_at", "expires_at"),)

    account_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_accounts.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    replaced_by_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("refresh_sessions.id", ondelete="SET NULL")
    )
    user_agent: Mapped[str | None] = mapped_column(String(500))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    account: Mapped[UserAccount] = relationship(back_populates="refresh_sessions")
