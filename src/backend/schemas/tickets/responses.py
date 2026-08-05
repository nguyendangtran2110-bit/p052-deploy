from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.backend.domain.tickets.enums import TicketPriority, TicketSource, TicketStatus


class TicketEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    actor_type: str
    actor_id: str | None
    from_status: str | None
    to_status: str | None
    comment: str | None
    payload: dict
    created_at: datetime


class TicketAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    mime_type: str | None
    size_bytes: int
    created_at: datetime


class TicketSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticket_code: str
    resident_id: UUID
    unit_id: UUID
    conversation_id: UUID | None
    source: TicketSource
    status: TicketStatus
    category: str
    priority: TicketPriority
    title: str
    description: str
    location: str
    submitted_at: datetime
    approved_at: datetime | None
    resolved_at: datetime | None
    assigned_to_id: UUID | None
    assigned_at: datetime | None
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TicketResponse(TicketSummaryResponse):
    events: list[TicketEventResponse] = Field(default_factory=list)
    attachments: list[TicketAttachmentResponse] = Field(default_factory=list)


class TicketListResponse(BaseModel):
    items: list[TicketSummaryResponse]
    total: int
    offset: int
    limit: int
