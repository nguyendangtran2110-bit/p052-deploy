from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.backend.domain.residents.enums import ResidentUnitRole


class ResidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resident_code: str
    full_name: str
    email: str | None
    phone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_code: str
    building: str
    floor: str | None
    unit_number: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ResidentUnitLinkResponse(BaseModel):
    resident_id: UUID
    unit_id: UUID
    role: ResidentUnitRole
    is_primary: bool


class ResidentUnitSummary(UnitResponse):
    resident_role: ResidentUnitRole
    is_primary: bool


class ResidentProfileResponse(ResidentResponse):
    units: list[ResidentUnitSummary]
