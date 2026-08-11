from uuid import UUID

from pydantic import BaseModel, Field


class AttachmentPresignRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(gt=0)
    ticket_id: UUID | None = None
