from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class AttachmentPresignRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(gt=0)
    ticket_id: UUID | None = None
    announcement_id: UUID | None = None

    @model_validator(mode="after")
    def validate_parent(self) -> "AttachmentPresignRequest":
        if self.ticket_id is not None and self.announcement_id is not None:
            raise ValueError("Attachment cannot be linked to both a ticket and an announcement")
        return self
