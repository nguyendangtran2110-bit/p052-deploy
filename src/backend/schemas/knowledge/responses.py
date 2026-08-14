from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.backend.domain.knowledge.enums import KnowledgeDocumentStatus, KnowledgeDocumentType


class KnowledgeDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    document_type: KnowledgeDocumentType
    version: str
    project_code: str | None
    building: str | None
    original_filename: str
    mime_type: str | None
    checksum_sha256: str
    status: KnowledgeDocumentStatus
    effective_date: date | None
    document_metadata: dict
    error_message: str | None
    indexed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentListResponse(BaseModel):
    items: list[KnowledgeDocumentResponse]
    total: int
    offset: int
    limit: int
