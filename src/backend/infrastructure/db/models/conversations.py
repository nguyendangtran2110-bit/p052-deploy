from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.domain.conversations.enums import (
    ConversationHandoffStatus,
    ConversationStatus,
    MessageRole,
)
from src.backend.infrastructure.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from src.backend.infrastructure.db.models.ai_workflows import AIWorkflow
    from src.backend.infrastructure.db.models.residents import Resident, Unit
    from src.backend.infrastructure.db.models.tickets import Ticket, TicketAttachment


class Conversation(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'closed')", name="ck_conversation_status"),
        CheckConstraint(
            "handoff_status IN ('bot_active', 'waiting_management', 'management_active')",
            name="ck_conversation_handoff_status",
        ),
        CheckConstraint(
            "conversation_type IN ('resident_support', 'manager_assistant')",
            name="ck_conversation_type",
        ),
        CheckConstraint(
            "workflow_type IS NULL OR workflow_type IN ('resident_ticket', 'manager_announcement')",
            name="ck_conversation_workflow_type",
        ),
    )

    resident_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("residents.id", ondelete="SET NULL"), index=True
    )
    unit_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("units.id", ondelete="SET NULL"), index=True)
    status: Mapped[str] = mapped_column(String(20), default=ConversationStatus.ACTIVE.value, nullable=False)
    handoff_status: Mapped[str] = mapped_column(
        String(30), default=ConversationHandoffStatus.BOT_ACTIVE.value, nullable=False, index=True
    )
    handoff_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_manager_id: Mapped[str | None] = mapped_column(String(100), index=True)
    conversation_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    conversation_type: Mapped[str] = mapped_column(
        String(30), default="resident_support", nullable=False, index=True
    )
    workflow_type: Mapped[str | None] = mapped_column(String(40), index=True)
    workflow_id: Mapped[str | None] = mapped_column(String(36), index=True)

    resident: Mapped[Resident | None] = relationship(back_populates="conversations")
    unit: Mapped[Unit | None] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )
    ticket: Mapped[Ticket | None] = relationship(back_populates="conversation", uselist=False)
    ai_workflow: Mapped[AIWorkflow | None] = relationship(
        back_populates="conversation", uselist=False, cascade="all, delete-orphan"
    )


class Message(UuidPrimaryKeyMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'management', 'system')", name="ck_message_role"),
        Index("ix_message_conversation_created", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20), default=MessageRole.USER.value, nullable=False)
    author_id: Mapped[str | None] = mapped_column(String(100), index=True)
    content: Mapped[str] = mapped_column(Text)
    intent: Mapped[str | None] = mapped_column(String(100))
    citations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    action_payload: Mapped[dict | None] = mapped_column(JSON)
    workflow_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("ai_workflows.id", ondelete="SET NULL"), index=True
    )
    workflow_state: Mapped[str | None] = mapped_column(String(40))
    workflow_version: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    attachments: Mapped[list[TicketAttachment]] = relationship(back_populates="message")

    @property
    def attachment_ids(self) -> list[str]:
        return [attachment.id for attachment in self.attachments]
