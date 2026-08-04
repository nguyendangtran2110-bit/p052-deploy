from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.domain.conversations.enums import ConversationStatus, MessageRole
from src.backend.infrastructure.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from src.backend.infrastructure.db.models.residents import Resident, Unit
    from src.backend.infrastructure.db.models.tickets import Ticket


class Conversation(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (CheckConstraint("status IN ('active', 'closed')", name="ck_conversation_status"),)

    resident_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("residents.id", ondelete="SET NULL"), index=True
    )
    unit_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("units.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(20), default=ConversationStatus.ACTIVE.value, nullable=False)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    resident: Mapped[Resident | None] = relationship(back_populates="conversations")
    unit: Mapped[Unit | None] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )
    tickets: Mapped[list[Ticket]] = relationship(back_populates="conversation")


class Message(UuidPrimaryKeyMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="ck_message_role"),
        Index("ix_message_conversation_created", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20), default=MessageRole.USER.value, nullable=False)
    content: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(100))
    citations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    action_payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
