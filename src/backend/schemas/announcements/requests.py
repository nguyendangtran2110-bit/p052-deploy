from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from src.backend.domain.announcements.enums import (
    AnnouncementPriority,
    AnnouncementScopeType,
    AnnouncementType,
)


class AnnouncementScopeRequest(BaseModel):
    scope_type: AnnouncementScopeType
    project_code: str | None = Field(default=None, min_length=1, max_length=50)
    building: str | None = Field(default=None, min_length=1, max_length=100)
    unit_id: UUID | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> "AnnouncementScopeRequest":
        if self.scope_type is AnnouncementScopeType.ALL_RESIDENTS:
            if self.project_code or self.building or self.unit_id:
                raise ValueError("all_residents scope cannot include project, building, or unit")
        elif self.scope_type is AnnouncementScopeType.PROJECT:
            if not self.project_code or self.building or self.unit_id:
                raise ValueError("project scope requires project_code only")
        elif self.scope_type is AnnouncementScopeType.BUILDING:
            if not self.building or self.unit_id:
                raise ValueError("building scope requires building and may include project_code")
        elif self.scope_type is AnnouncementScopeType.UNIT and self.unit_id is None:
            raise ValueError("unit scope requires unit_id")
        return self


class AnnouncementCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    content: str = Field(min_length=2, max_length=50000)
    type: AnnouncementType = AnnouncementType.GENERAL
    priority: AnnouncementPriority = AnnouncementPriority.NORMAL
    expires_at: datetime | None = None
    scopes: list[AnnouncementScopeRequest] = Field(default_factory=list, max_length=50)
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=20)


class AnnouncementUpdateRequest(BaseModel):
    version: int = Field(ge=0)
    title: str | None = Field(default=None, min_length=2, max_length=255)
    content: str | None = Field(default=None, min_length=2, max_length=50000)
    type: AnnouncementType | None = None
    priority: AnnouncementPriority | None = None
    expires_at: datetime | None = None
    scopes: list[AnnouncementScopeRequest] | None = Field(default=None, max_length=50)
    attachment_ids: list[UUID] | None = Field(default=None, max_length=20)


class AnnouncementVersionRequest(BaseModel):
    version: int = Field(ge=0)
