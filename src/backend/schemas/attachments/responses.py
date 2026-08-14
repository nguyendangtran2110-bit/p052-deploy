from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AttachmentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    mime_type: str | None
    size_bytes: int
    object_key: str
    upload_url: str
    expires_in: int
    created_at: datetime


class AttachmentDownloadResponse(BaseModel):
    id: UUID
    filename: str
    download_url: str
    expires_in: int
