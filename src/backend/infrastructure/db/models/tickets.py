from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.domain.tickets.enums import TicketPriority, TicketSource, TicketStatus
from src.backend.infrastructure.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from src.backend.infrastructure.db.models.conversations import Conversation
    from src.backend.infrastructure.db.models.identity import UserAccount
    from src.backend.infrastructure.db.models.residents import Resident, Unit


class Ticket(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint("source IN ('form', 'chat')", name="ck_ticket_source"),
        CheckConstraint(
            "status IN ('submitted', 'approved', 'in_progress', 'resolved', 'rejected', 'cancelled')",
            name="ck_ticket_status",
        ),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name="ck_ticket_priority"),
        UniqueConstraint("resident_id", "idempotency_key", name="uq_ticket_resident_idempotency"),
        Index("ix_ticket_resident_status", "resident_id", "status"),
        Index("ix_ticket_unit_status", "unit_id", "status"),
        Index("ix_ticket_assignee_status", "assigned_to_id", "status"),
    )

    ticket_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    resident_id: Mapped[str] = mapped_column(String(36), ForeignKey("residents.id"), index=True)
    unit_id: Mapped[str] = mapped_column(String(36), ForeignKey("units.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="SET NULL"), index=True
    )
    source: Mapped[str] = mapped_column(String(20), default=TicketSource.FORM.value, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=TicketStatus.SUBMITTED.value, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True)
    priority: Mapped[str] = mapped_column(String(20), default=TicketPriority.MEDIUM.value, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(255))
    idempotency_key: Mapped[str | None] = mapped_column(String(100))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_to_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user_accounts.id", ondelete="SET NULL"), index=True
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    resident: Mapped[Resident] = relationship(back_populates="tickets")
    unit: Mapped[Unit] = relationship(back_populates="tickets")
    conversation: Mapped[Conversation | None] = relationship(back_populates="tickets")
    assignee: Mapped[UserAccount | None] = relationship()
    events: Mapped[list[TicketEvent]] = relationship(
        back_populates="ticket", cascade="all, delete-orphan", order_by="TicketEvent.created_at"
    )
    attachments: Mapped[list[TicketAttachment]] = relationship(back_populates="ticket", cascade="all, delete-orphan")


class TicketEvent(UuidPrimaryKeyMixin, Base):
    __tablename__ = "ticket_events"
    __table_args__ = (
        CheckConstraint(
            "actor_type IN ('anonymous', 'resident', 'management', 'system')", name="ck_ticket_event_actor_type"
        ),
        Index("ix_ticket_event_ticket_created", "ticket_id", "created_at"),
    )

    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    actor_type: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str | None] = mapped_column(String(100))
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str | None] = mapped_column(String(30))
    comment: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="events")


class TicketAttachment(UuidPrimaryKeyMixin, Base):
    __tablename__ = "ticket_attachments"

    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    ticket: Mapped[Ticket] = relationship(back_populates="attachments")
