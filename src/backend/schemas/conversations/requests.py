from uuid import UUID

from pydantic import BaseModel, Field


class ManagementConversationMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    conversation_version: int | None = Field(default=None, ge=0)
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=10)


class ManagementConversationHandbackRequest(BaseModel):
    conversation_version: int | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=1000)


class ManagementConversationTakeoverRequest(BaseModel):
    conversation_version: int = Field(ge=0)
    note: str | None = Field(default=None, max_length=1000)
