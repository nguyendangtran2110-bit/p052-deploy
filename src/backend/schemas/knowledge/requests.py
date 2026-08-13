from pydantic import BaseModel, Field

from src.backend.domain.knowledge.enums import KnowledgeDocumentStatus


class KnowledgeDocumentStatusUpdate(BaseModel):
    status: KnowledgeDocumentStatus
    error_message: str | None = Field(default=None, max_length=2000)
