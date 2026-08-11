from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import require_authenticated
from src.backend.application.attachments.service import AttachmentService
from src.backend.core.config import Settings, get_settings
from src.backend.domain.common.auth import ActorContext
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.attachments import (
    AttachmentDownloadResponse,
    AttachmentPresignRequest,
    AttachmentUploadResponse,
)

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.post("/presign", response_model=AttachmentUploadResponse, status_code=status.HTTP_201_CREATED)
async def presign_attachment_upload(
    payload: AttachmentPresignRequest,
    actor: ActorContext = Depends(require_authenticated),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AttachmentUploadResponse:
    attachment, upload_url = await AttachmentService(session, settings).create_upload(
        filename=payload.filename,
        mime_type=payload.content_type,
        size_bytes=payload.size_bytes,
        ticket_id=str(payload.ticket_id) if payload.ticket_id else None,
        actor=actor,
    )
    return AttachmentUploadResponse(
        id=attachment.id,
        filename=attachment.filename,
        mime_type=attachment.mime_type,
        size_bytes=attachment.size_bytes,
        object_key=attachment.storage_path,
        upload_url=upload_url,
        expires_in=settings.s3_presigned_url_expire_seconds,
        created_at=attachment.created_at,
    )


@router.get("/{attachment_id}/download", response_model=AttachmentDownloadResponse)
async def presign_attachment_download(
    attachment_id: UUID,
    actor: ActorContext = Depends(require_authenticated),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AttachmentDownloadResponse:
    attachment, download_url = await AttachmentService(session, settings).create_download(str(attachment_id), actor)
    return AttachmentDownloadResponse(
        id=attachment.id,
        filename=attachment.filename,
        download_url=download_url,
        expires_in=settings.s3_presigned_url_expire_seconds,
    )
