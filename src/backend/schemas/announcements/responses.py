from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.backend.domain.announcements.enums import (
    AnnouncementPriority,
    AnnouncementScopeType,
    AnnouncementStatus,
    AnnouncementType,
)


class AnnouncementScopeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    scope_type: AnnouncementScopeType
    project_code: str | None
    building: str | None
    unit_id: UUID | None


class AnnouncementAttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    mime_type: str | None
    size_bytes: int
    created_at: datetime


class AnnouncementEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    actor_type: str
    actor_id: str | None
    from_status: AnnouncementStatus | None
    to_status: AnnouncementStatus | None
    payload: dict
    created_at: datetime


class AnnouncementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    announcement_code: str
    title: str
    content: str
    type: AnnouncementType
    priority: AnnouncementPriority
    status: AnnouncementStatus
    author_id: str | None
    published_at: datetime | None
    expires_at: datetime | None
    version: int
    is_read: bool = False
    scopes: list[AnnouncementScopeResponse] = Field(default_factory=list)
    attachments: list[AnnouncementAttachmentResponse] = Field(default_factory=list)
    events: list[AnnouncementEventResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AnnouncementListResponse(BaseModel):
    items: list[AnnouncementResponse]
    total: int
    offset: int
    limit: int


class AnnouncementUnreadCountResponse(BaseModel):
    unread_count: int


class AnnouncementReadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    announcement_id: UUID
    resident_id: UUID
    read_at: datetime


class AnnouncementStatisticsResponse(BaseModel):
    announcement_id: UUID
    eligible_resident_count: int
    read_count: int
    unread_count: int
