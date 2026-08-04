from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    conversation_id: UUID | None = None
    unit_id: UUID | None = None
    confirm_action: bool = False
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=100)
