from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.domain.ai_workflows.enums import AIWorkflowActionStatus, AIWorkflowState
from src.backend.infrastructure.db.base import Base, TimestampMixin, UuidPrimaryKeyMixin, utc_now

if TYPE_CHECKING:
    from src.backend.infrastructure.db.models.conversations import Conversation
    from src.backend.infrastructure.db.models.residents import Resident
    from src.backend.infrastructure.db.models.tickets import TicketAttachment


class AIWorkflow(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_workflows"
    __table_args__ = (
        UniqueConstraint("conversation_id", name="uq_ai_workflow_conversation"),
        CheckConstraint(
            "workflow_type IN ('resident_ticket', 'manager_announcement')",
            name="ck_ai_workflow_type",
        ),
        CheckConstraint(
            "state IN ('collecting', 'awaiting_confirmation', 'executing', 'completed', 'cancelled', 'failed', "
            "'awaiting_publish_confirmation', 'publishing', 'published')",
            name="ck_ai_workflow_state",
        ),
        Index("ix_ai_workflow_conversation_updated", "conversation_id", "updated_at"),
        Index("ix_ai_workflow_owner_state", "owner_actor_id", "state"),
    )

    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workflow_type: Mapped[str] = mapped_column(String(40), nullable=False)
    owner_actor_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    owner_resident_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("residents.id", ondelete="SET NULL"), index=True
    )
    state: Mapped[str] = mapped_column(String(40), default=AIWorkflowState.COLLECTING.value, nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    draft: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    missing_fields: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    pending_action: Mapped[dict | None] = mapped_column(JSON)
    attachment_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSON)
    last_error: Mapped[dict | None] = mapped_column(JSON)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    conversation: Mapped[Conversation] = relationship(back_populates="ai_workflow")
    owner_resident: Mapped[Resident | None] = relationship()
    actions: Mapped[list[AIWorkflowAction]] = relationship(
        back_populates="workflow", cascade="all, delete-orphan", order_by="AIWorkflowAction.created_at"
    )
    attachments: Mapped[list[TicketAttachment]] = relationship(back_populates="workflow")


class AIWorkflowAction(UuidPrimaryKeyMixin, Base):
    __tablename__ = "ai_workflow_actions"
    __table_args__ = (
        UniqueConstraint("workflow_id", "action_id", name="uq_ai_workflow_action_id"),
        CheckConstraint(
            "status IN ('pending', 'executing', 'succeeded', 'failed', 'unknown', 'cancelled')",
            name="ck_ai_workflow_action_status",
        ),
        Index("ix_ai_workflow_action_workflow_created", "workflow_id", "created_at"),
    )

    workflow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_workflows.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action_type: Mapped[str] = mapped_column(String(60), nullable=False)
    workflow_version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=AIWorkflowActionStatus.PENDING.value, nullable=False)
    request_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    response_payload: Mapped[dict | None] = mapped_column(JSON)
    error_payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    workflow: Mapped[AIWorkflow] = relationship(back_populates="actions")
