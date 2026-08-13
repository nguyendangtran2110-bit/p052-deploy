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
    announcement: Any | None = None
    workflow_id: UUID | None = None
    workflow_type: str | None = None
    state: str | None = None
    workflow_version: int | None = None
    draft: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    message: dict[str, Any] | None = None
