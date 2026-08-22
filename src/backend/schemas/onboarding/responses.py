from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.backend.domain.onboarding.enums import OnboardingCategory, OnboardingItemStatus, OnboardingItemType


class OnboardingUnitResponse(BaseModel):
    id: UUID
    project_code: str
    building: str
    floor: str | None
    unit_number: str


class OnboardingItemResponse(BaseModel):
    id: UUID
    code: str
    category: OnboardingCategory
    item_type: OnboardingItemType
    title: str
    summary: str
    handbook_reference: str | None
    is_required: bool
    sort_order: int
    status: OnboardingItemStatus
    acted_at: datetime | None
    updated_at: datetime


class OnboardingChecklistResponse(BaseModel):
    id: UUID
    resident_id: UUID
    unit_id: UUID
    unit: OnboardingUnitResponse
    progress_percent: int
    required_item_count: int
    completed_item_count: int
    completed_at: datetime | None
    updated_at: datetime
    items: list[OnboardingItemResponse]


class OnboardingListResponse(BaseModel):
    items: list[OnboardingChecklistResponse]


class ManagementOnboardingChecklistResponse(OnboardingChecklistResponse):
    resident_code: str
    resident_name: str


class ManagementOnboardingListResponse(BaseModel):
    items: list[ManagementOnboardingChecklistResponse]
    total: int
    offset: int
    limit: int
