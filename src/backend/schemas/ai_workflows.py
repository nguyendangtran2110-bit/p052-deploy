from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.backend.schemas.announcements import AnnouncementResponse
from src.backend.schemas.tickets import TicketResponse


class AIWorkflowConversationCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}


class AIWorkflowMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    workflow_id: UUID | None = None
    workflow_version: int | None = Field(default=None, ge=0)
    confirmed_action_id: UUID | None = None
    confirm_action: bool = False
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=100)
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=10)


class AIWorkflowMessageResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    role: str
    author_id: str | None
    content: str
    intent: str | None = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    action_payload: dict[str, Any] | None = None
    attachment_ids: list[UUID] = Field(default_factory=list)
    workflow_id: UUID | None = None
    workflow_state: str | None = None
    workflow_version: int | None = None
    created_at: datetime


class AIWorkflowResponse(BaseModel):
    conversation_id: UUID
    workflow_id: UUID
    workflow_type: str
    state: str
    workflow_version: int
    message: AIWorkflowMessageResponse | None = None
    draft: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    action: dict[str, Any] | None = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    ticket: TicketResponse | None = None
    announcement: AnnouncementResponse | None = None
    error: dict[str, Any] | None = None


class AIWorkflowConversationResponse(BaseModel):
    conversation_id: UUID
    workflow_id: UUID
    workflow_type: str
    state: str
    workflow_version: int
    messages: list[AIWorkflowMessageResponse] = Field(default_factory=list)
    draft: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    action: dict[str, Any] | None = None
    ticket: TicketResponse | None = None
    announcement: AnnouncementResponse | None = None
    error: dict[str, Any] | None = None


class AIWorkflowCancelResponse(BaseModel):
    workflow_id: UUID
    state: str
    workflow_version: int
