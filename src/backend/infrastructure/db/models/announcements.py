from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.domain.announcements.enums import (
    AnnouncementPriority,
    AnnouncementStatus,
    AnnouncementType,
)
from src.backend.infrastructure.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from src.backend.infrastructure.db.models.residents import Resident, Unit
    from src.backend.infrastructure.db.models.tickets import TicketAttachment


class Announcement(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "announcements"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'archived')",
            name="ck_announcement_status",
        ),
        CheckConstraint(
            "type IN ('general', 'maintenance', 'facility', 'regulation_update', 'event', 'emergency')",
            name="ck_announcement_type",
        ),
        CheckConstraint(
            "priority IN ('normal', 'important', 'urgent')",
            name="ck_announcement_priority",
        ),
        Index("ix_announcement_status_published_at", "status", "published_at"),
        Index("ix_announcement_author_status", "author_id", "status"),
    )

    announcement_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(30), default=AnnouncementType.GENERAL.value, index=True, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(20), default=AnnouncementPriority.NORMAL.value, index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default=AnnouncementStatus.DRAFT.value, index=True, nullable=False)
    # This is intentionally a string rather than a foreign key: local dev auth can use synthetic actor IDs.
    author_id: Mapped[str | None] = mapped_column(String(100), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    scopes: Mapped[list[AnnouncementScope]] = relationship(
        back_populates="announcement", cascade="all, delete-orphan", order_by="AnnouncementScope.created_at"
    )
    reads: Mapped[list[AnnouncementRead]] = relationship(
        back_populates="announcement", cascade="all, delete-orphan"
    )
    events: Mapped[list[AnnouncementEvent]] = relationship(
        back_populates="announcement", cascade="all, delete-orphan", order_by="AnnouncementEvent.created_at"
    )
    attachments: Mapped[list[TicketAttachment]] = relationship(back_populates="announcement")


class AnnouncementScope(UuidPrimaryKeyMixin, Base):
    __tablename__ = "announcement_scopes"
    __table_args__ = (
        CheckConstraint(
            "scope_type IN ('all_residents', 'project', 'building', 'unit')",
            name="ck_announcement_scope_type",
        ),
        Index("ix_announcement_scope_announcement_type", "announcement_id", "scope_type"),
    )

    announcement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("announcements.id", ondelete="CASCADE"), index=True
    )
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False)
    project_code: Mapped[str | None] = mapped_column(String(50), index=True)
    building: Mapped[str | None] = mapped_column(String(100), index=True)
    unit_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("units.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    announcement: Mapped[Announcement] = relationship(back_populates="scopes")
    unit: Mapped[Unit | None] = relationship()


class AnnouncementRead(UuidPrimaryKeyMixin, Base):
    __tablename__ = "announcement_reads"
    __table_args__ = (
        UniqueConstraint("announcement_id", "resident_id", name="uq_announcement_read_resident"),
        Index("ix_announcement_read_announcement", "announcement_id", "read_at"),
        Index("ix_announcement_read_resident", "resident_id", "read_at"),
    )

    announcement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("announcements.id", ondelete="CASCADE"), index=True
    )
    resident_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("residents.id", ondelete="CASCADE"), index=True
    )
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    announcement: Mapped[Announcement] = relationship(back_populates="reads")
    resident: Mapped[Resident] = relationship()


class AnnouncementEvent(UuidPrimaryKeyMixin, Base):
    __tablename__ = "announcement_events"
    __table_args__ = (
        CheckConstraint(
            "actor_type IN ('anonymous', 'resident', 'management', 'system')",
            name="ck_announcement_event_actor_type",
        ),
        Index("ix_announcement_event_announcement_created", "announcement_id", "created_at"),
    )

    announcement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("announcements.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(100))
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str | None] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    announcement: Mapped[Announcement] = relationship(back_populates="events")
