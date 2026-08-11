from uuid import UUID

from pydantic import BaseModel, Field

from src.backend.domain.tickets.enums import TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    unit_id: UUID
    category: str = Field(min_length=2, max_length=100)
    priority: TicketPriority = TicketPriority.MEDIUM
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=5, max_length=5000)
    location: str = Field(min_length=2, max_length=255)
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=10)


class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    comment: str | None = Field(default=None, max_length=2000)
