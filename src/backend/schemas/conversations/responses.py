from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.backend.domain.conversations.enums import ConversationHandoffStatus, ConversationStatus, MessageRole
from src.backend.schemas.tickets import TicketResponse


class ConversationMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: MessageRole
    author_id: str | None
    content: str
    intent: str | None
    citations: list[dict] = Field(default_factory=list)
    action_payload: dict | None
    attachment_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime
    conversation_version: int | None = None


class ConversationHandoffResponse(BaseModel):
    conversation_id: UUID
    handoff_status: ConversationHandoffStatus
    handoff_requested_at: datetime | None
    assigned_manager_id: str | None
    conversation_version: int
    message: ConversationMessageResponse


class ConversationAssignmentResponse(BaseModel):
    conversation_id: UUID
    handoff_status: ConversationHandoffStatus
    assigned_manager_id: str | None
    conversation_version: int
    message: ConversationMessageResponse | None = None


class TicketConversationResponse(BaseModel):
    conversation_id: UUID
    status: ConversationStatus
    handoff_status: ConversationHandoffStatus
    handoff_requested_at: datetime | None
    assigned_manager_id: str | None
    conversation_version: int
    last_message_at: datetime
    ticket: TicketResponse
    messages: list[ConversationMessageResponse]


class ConversationResponse(BaseModel):
    conversation_id: UUID
    resident_id: UUID | None
    unit_id: UUID | None
    status: ConversationStatus
    handoff_status: ConversationHandoffStatus
    handoff_requested_at: datetime | None
    assigned_manager_id: str | None
    conversation_version: int
    last_message_at: datetime
    ticket: TicketResponse | None
    messages: list[ConversationMessageResponse]


class ConversationSummaryResponse(BaseModel):
    conversation_id: UUID
    resident_id: UUID
    unit_id: UUID | None
    status: ConversationStatus
    handoff_status: ConversationHandoffStatus
    handoff_requested_at: datetime | None
    assigned_manager_id: str | None
    conversation_version: int
    last_message_at: datetime
    ticket_id: UUID | None
    ticket_code: str | None


class ConversationListResponse(BaseModel):
    items: list[ConversationSummaryResponse]
    total: int
    offset: int
    limit: int
