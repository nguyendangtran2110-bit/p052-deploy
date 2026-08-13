from dataclasses import dataclass
from datetime import datetime

from src.backend.domain.announcements.enums import (
    AnnouncementPriority,
    AnnouncementScopeType,
    AnnouncementType,
)


@dataclass(frozen=True, slots=True)
class AnnouncementScopeCommand:
    scope_type: AnnouncementScopeType
    project_code: str | None = None
    building: str | None = None
    unit_id: str | None = None


@dataclass(frozen=True, slots=True)
class CreateAnnouncementCommand:
    title: str
    content: str
    announcement_type: AnnouncementType
    priority: AnnouncementPriority
    expires_at: datetime | None
    scopes: tuple[AnnouncementScopeCommand, ...] = ()
    attachment_ids: tuple[str, ...] = ()
    action_id: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateAnnouncementCommand:
    version: int
    changed_fields: frozenset[str]
    title: str | None = None
    content: str | None = None
    announcement_type: AnnouncementType | None = None
    priority: AnnouncementPriority | None = None
    expires_at: datetime | None = None
    scopes: tuple[AnnouncementScopeCommand, ...] | None = None
    attachment_ids: tuple[str, ...] | None = None
