from uuid import UUID

from pydantic import BaseModel, Field

from src.backend.domain.residents.enums import ResidentUnitRole


class ResidentCreate(BaseModel):
    resident_code: str = Field(min_length=2, max_length=50)
    full_name: str = Field(min_length=2, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, min_length=8, max_length=30)


class UnitCreate(BaseModel):
    project_code: str = Field(min_length=1, max_length=50)
    building: str = Field(min_length=1, max_length=100)
    floor: str | None = Field(default=None, max_length=20)
    unit_number: str = Field(min_length=1, max_length=50)


class ResidentUnitLinkCreate(BaseModel):
    unit_id: UUID
    role: ResidentUnitRole = ResidentUnitRole.OWNER
    is_primary: bool = False
