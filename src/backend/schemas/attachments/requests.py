from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class AttachmentPresignRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(gt=0)
    ticket_id: UUID | None = None
    announcement_id: UUID | None = None
    workflow_id: UUID | None = None

    @model_validator(mode="after")
    def validate_parent(self) -> "AttachmentPresignRequest":
        parents = [value for value in (self.ticket_id, self.announcement_id, self.workflow_id) if value is not None]
        if len(parents) > 1:
            raise ValueError("Attachment cannot be linked to more than one parent")
        return self
