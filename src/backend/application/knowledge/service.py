import asyncio
import hashlib
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.config import Settings
from src.backend.domain.common.errors import ConflictError, NotFoundError, ValidationError
from src.backend.domain.knowledge.enums import KnowledgeDocumentStatus, KnowledgeDocumentType
from src.backend.infrastructure.db.models import KnowledgeDocument
from src.backend.infrastructure.db.repositories import KnowledgeRepository

ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


class KnowledgeService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.documents = KnowledgeRepository(session)

    async def upload(
        self,
        *,
        content: bytes,
        original_filename: str,
        mime_type: str | None,
        title: str,
        document_type: KnowledgeDocumentType,
        version: str,
        project_code: str | None,
        building: str | None,
        effective_date: date | None,
    ) -> KnowledgeDocument:
        safe_name = Path(original_filename).name
        suffix = Path(safe_name).suffix.lower()
        if suffix not in ALLOWED_DOCUMENT_EXTENSIONS:
            raise ValidationError("Only PDF, DOCX, TXT and Markdown handbooks are supported")
        if not content:
            raise ValidationError("Uploaded handbook is empty")
        if len(content) > self.settings.max_upload_bytes:
            raise ValidationError(f"Uploaded handbook exceeds {self.settings.max_upload_bytes} bytes")

        checksum = hashlib.sha256(content).hexdigest()
        duplicate = await self.documents.get_by_checksum(checksum)
        if duplicate:
            raise ConflictError(f"This document was already uploaded as {duplicate.id}")

        storage_dir = self.settings.knowledge_storage_dir
        await asyncio.to_thread(storage_dir.mkdir, parents=True, exist_ok=True)
        target = storage_dir / f"{uuid4()}{suffix}"
        await asyncio.to_thread(target.write_bytes, content)

        document = KnowledgeDocument(
            title=title,
            document_type=document_type.value,
            version=version,
            project_code=project_code,
            building=building,
            source_path=str(target),
            original_filename=safe_name,
            mime_type=mime_type,
            checksum_sha256=checksum,
            status=KnowledgeDocumentStatus.PENDING.value,
            effective_date=effective_date,
        )
        try:
            await self.documents.add(document)
            await self.session.commit()
        except Exception:
            await asyncio.to_thread(target.unlink, missing_ok=True)
            raise
        return document

    async def get(self, document_id: str) -> KnowledgeDocument:
        document = await self.documents.get(document_id)
        if document is None:
            raise NotFoundError("Knowledge document was not found")
        return document

    async def list(self, **filters):
        return await self.documents.list(**filters)

    async def update_status(
        self,
        document_id: str,
        status: KnowledgeDocumentStatus,
        error_message: str | None = None,
    ) -> KnowledgeDocument:
        document = await self.get(document_id)
        document.status = status.value
        document.error_message = error_message
        if status is KnowledgeDocumentStatus.INDEXED:
            document.indexed_at = datetime.now(UTC)
        await self.session.commit()
        return document
