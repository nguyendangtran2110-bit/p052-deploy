from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import require_manager_or_admin, require_resident
from src.backend.application.announcements.contracts import (
    AnnouncementScopeCommand,
    CreateAnnouncementCommand,
    UpdateAnnouncementCommand,
)
from src.backend.application.announcements.service import AnnouncementService
from src.backend.domain.announcements.enums import (
    AnnouncementPriority,
    AnnouncementStatus,
    AnnouncementType,
)
from src.backend.domain.common.auth import ActorContext
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.announcements import (
    AnnouncementAttachmentResponse,
    AnnouncementCreateRequest,
    AnnouncementEventResponse,
    AnnouncementListResponse,
    AnnouncementReadResponse,
    AnnouncementResponse,
    AnnouncementScopeResponse,
    AnnouncementStatisticsResponse,
    AnnouncementUnreadCountResponse,
    AnnouncementUpdateRequest,
    AnnouncementVersionRequest,
)

resident_router = APIRouter(prefix="/announcements", tags=["announcements"])
management_router = APIRouter(prefix="/management/announcements", tags=["management-announcements"])


def _scope_commands(scopes) -> tuple[AnnouncementScopeCommand, ...]:
    return tuple(
        AnnouncementScopeCommand(
            scope_type=scope.scope_type,
            project_code=scope.project_code,
            building=scope.building,
            unit_id=str(scope.unit_id) if scope.unit_id else None,
        )
        for scope in scopes
    )


def _announcement_response(
    announcement,
    *,
    is_read: bool = False,
    include_events: bool = False,
) -> AnnouncementResponse:
    return AnnouncementResponse(
        id=announcement.id,
        announcement_code=announcement.announcement_code,
        title=announcement.title,
        content=announcement.content,
        type=announcement.type,
        priority=announcement.priority,
        status=announcement.status,
        author_id=announcement.author_id,
        published_at=announcement.published_at,
        expires_at=announcement.expires_at,
        version=announcement.version,
        is_read=is_read,
        scopes=[AnnouncementScopeResponse.model_validate(scope) for scope in announcement.scopes],
        attachments=[
            AnnouncementAttachmentResponse.model_validate(attachment) for attachment in announcement.attachments
        ],
        events=(
            [
                AnnouncementEventResponse.model_validate(event)
                for event in sorted(announcement.events, key=lambda event: event.created_at)
            ]
            if include_events
            else []
        ),
        created_at=announcement.created_at,
        updated_at=announcement.updated_at,
    )


@resident_router.get("", response_model=AnnouncementListResponse)
async def list_announcements(
    unread_only: bool = Query(default=False),
    announcement_type: AnnouncementType | None = Query(default=None, alias="type"),
    priority: AnnouncementPriority | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    actor: ActorContext = Depends(require_resident),
    session: AsyncSession = Depends(get_db_session),
) -> AnnouncementListResponse:
    items, total = await AnnouncementService(session).list_resident(
        actor,
        unread_only=unread_only,
        announcement_type=announcement_type,
        priority=priority,
        offset=offset,
        limit=limit,
    )
    return AnnouncementListResponse(
        items=[_announcement_response(item, is_read=is_read) for item, is_read in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@resident_router.get("/unread-count", response_model=AnnouncementUnreadCountResponse)
async def get_unread_announcement_count(
    actor: ActorContext = Depends(require_resident),
    session: AsyncSession = Depends(get_db_session),
) -> AnnouncementUnreadCountResponse:
    return AnnouncementUnreadCountResponse(unread_count=await AnnouncementService(session).unread_count(actor))


@resident_router.get("/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: UUID,
    actor: ActorContext = Depends(require_resident),
    session: AsyncSession = Depends(get_db_session),
) -> AnnouncementResponse:
    announcement, is_read = await AnnouncementService(session).get_resident(str(announcement_id), actor)
    return _announcement_response(announcement, is_read=is_read)


@resident_router.post("/{announcement_id}/read", response_model=AnnouncementReadResponse)
async def mark_announcement_read(
    announcement_id: UUID,
    actor: ActorContext = Depends(require_resident),
    session: AsyncSession = Depends(get_db_session),
) -> AnnouncementReadResponse:
    read = await AnnouncementService(session).mark_read(str(announcement_id), actor)
    return AnnouncementReadResponse.model_validate(read)


@management_router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    request: AnnouncementCreateRequest,
    actor: ActorContext = Depends(require_manager_or_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AnnouncementResponse:
    announcement = await AnnouncementService(session).create(
        CreateAnnouncementCommand(
            title=request.title,
            content=request.content,
            announcement_type=request.type,
            priority=request.priority,
            expires_at=request.expires_at,
            scopes=_scope_commands(request.scopes),
            attachment_ids=tuple(str(attachment_id) for attachment_id in request.attachment_ids),
        ),
        actor,
    )
    return _announcement_response(announcement, include_events=True)


@management_router.get("", response_model=AnnouncementListResponse)
async def list_management_announcements(
    announcement_status: AnnouncementStatus | None = Query(default=None, alias="status"),
    announcement_type: AnnouncementType | None = Query(default=None, alias="type"),
    priority: AnnouncementPriority | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    actor: ActorContext = Depends(require_manager_or_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AnnouncementListResponse:
    items, total = await AnnouncementService(session).list_management(
        actor,
        status=announcement_status,
        announcement_type=announcement_type,
        priority=priority,
        offset=offset,
        limit=limit,
    )
    return AnnouncementListResponse(
        items=[_announcement_response(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@management_router.get("/{announcement_id}", response_model=AnnouncementResponse)
async def get_management_announcement(
    announcement_id: UUID,
    actor: ActorContext = Depends(require_manager_or_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AnnouncementResponse:
    announcement = await AnnouncementService(session).get_management(str(announcement_id), actor)
    return _announcement_response(announcement, include_events=True)


@management_router.patch("/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: UUID,
    request: AnnouncementUpdateRequest,
    actor: ActorContext = Depends(require_manager_or_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AnnouncementResponse:
    announcement = await AnnouncementService(session).update(
        str(announcement_id),
        UpdateAnnouncementCommand(
            version=request.version,
            changed_fields=frozenset(request.model_fields_set),
            title=request.title,
            content=request.content,
            announcement_type=request.type,
            priority=request.priority,
            expires_at=request.expires_at,
            scopes=_scope_commands(request.scopes) if request.scopes is not None else None,
            attachment_ids=(
                tuple(str(attachment_id) for attachment_id in request.attachment_ids)
                if request.attachment_ids is not None
                else None
            ),
        ),
        actor,
    )
    return _announcement_response(announcement, include_events=True)


@management_router.post("/{announcement_id}/publish", response_model=AnnouncementResponse)
async def publish_announcement(
    announcement_id: UUID,
    request: AnnouncementVersionRequest,
    actor: ActorContext = Depends(require_manager_or_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AnnouncementResponse:
    announcement = await AnnouncementService(session).publish(str(announcement_id), request.version, actor)
    return _announcement_response(announcement, include_events=True)


@management_router.post("/{announcement_id}/archive", response_model=AnnouncementResponse)
async def archive_announcement(
    announcement_id: UUID,
    request: AnnouncementVersionRequest,
    actor: ActorContext = Depends(require_manager_or_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AnnouncementResponse:
    announcement = await AnnouncementService(session).archive(str(announcement_id), request.version, actor)
    return _announcement_response(announcement, include_events=True)


@management_router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: UUID,
    actor: ActorContext = Depends(require_manager_or_admin),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    await AnnouncementService(session).delete_draft(str(announcement_id), actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@management_router.get("/{announcement_id}/statistics", response_model=AnnouncementStatisticsResponse)
async def get_announcement_statistics(
    announcement_id: UUID,
    actor: ActorContext = Depends(require_manager_or_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AnnouncementStatisticsResponse:
    data = await AnnouncementService(session).statistics(str(announcement_id), actor)
    return AnnouncementStatisticsResponse.model_validate(data)
