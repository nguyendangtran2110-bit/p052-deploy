from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import require_management
from src.backend.application.knowledge.service import KnowledgeService
from src.backend.core.config import Settings, get_settings
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.knowledge.enums import KnowledgeDocumentStatus, KnowledgeDocumentType
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.knowledge import (
    KnowledgeDocumentListResponse,
    KnowledgeDocumentResponse,
    KnowledgeDocumentStatusUpdate,
)

router = APIRouter(prefix="/knowledge/documents", tags=["knowledge"])


@router.post("", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form(min_length=2, max_length=255)],
    document_type: Annotated[KnowledgeDocumentType, Form()] = KnowledgeDocumentType.HANDBOOK,
    version: Annotated[str, Form(min_length=1, max_length=50)] = "1.0",
    project_code: Annotated[str | None, Form(max_length=50)] = None,
    building: Annotated[str | None, Form(max_length=100)] = None,
    effective_date: Annotated[date | None, Form()] = None,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    _actor: ActorContext = Depends(require_management),
) -> KnowledgeDocumentResponse:
    content = await file.read(settings.max_upload_bytes + 1)
    document = await KnowledgeService(session, settings).upload(
        content=content,
        original_filename=file.filename or "handbook",
        mime_type=file.content_type,
        title=title,
        document_type=document_type,
        version=version,
        project_code=project_code,
        building=building,
        effective_date=effective_date,
    )
    return KnowledgeDocumentResponse.model_validate(document)


@router.get("", response_model=KnowledgeDocumentListResponse)
async def list_documents(
    document_status: KnowledgeDocumentStatus | None = Query(default=None, alias="status"),
    document_type: KnowledgeDocumentType | None = None,
    project_code: str | None = None,
    building: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    _actor: ActorContext = Depends(require_management),
) -> KnowledgeDocumentListResponse:
    items, total = await KnowledgeService(session, settings).list(
        status=document_status.value if document_status else None,
        document_type=document_type.value if document_type else None,
        project_code=project_code,
        building=building,
        offset=offset,
        limit=limit,
    )
    return KnowledgeDocumentListResponse(
        items=[KnowledgeDocumentResponse.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{document_id}", response_model=KnowledgeDocumentResponse)
async def get_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    _actor: ActorContext = Depends(require_management),
) -> KnowledgeDocumentResponse:
    document = await KnowledgeService(session, settings).get(str(document_id))
    return KnowledgeDocumentResponse.model_validate(document)


@router.patch("/{document_id}/status", response_model=KnowledgeDocumentResponse)
async def update_document_status(
    document_id: UUID,
    request: KnowledgeDocumentStatusUpdate,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    _actor: ActorContext = Depends(require_management),
) -> KnowledgeDocumentResponse:
    document = await KnowledgeService(session, settings).update_status(
        str(document_id), request.status, request.error_message
    )
    return KnowledgeDocumentResponse.model_validate(document)
