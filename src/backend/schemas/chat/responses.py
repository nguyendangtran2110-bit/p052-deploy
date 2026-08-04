from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.backend.schemas.tickets import TicketResponse


class ChatMessageResponse(BaseModel):
    conversation_id: UUID
    response: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    action: dict[str, Any] | None = None
    ticket: TicketResponse | None = None
