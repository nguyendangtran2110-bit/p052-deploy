from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.backend.domain.identity.enums import AccountStatus, ActorRole, ManagementRole


class ManagementProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_code: str
    full_name: str
    phone: str | None
    department: str | None
    job_title: str | None
    management_role: ManagementRole
    project_code: str | None
    building: str | None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: ActorRole
    status: AccountStatus
    resident_id: UUID | None
    last_login_at: datetime | None
    email_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
    management_profile: ManagementProfileResponse | None = None


class TokenResponse(BaseModel):
    token_type: str = "bearer"
    access_token: str
    refresh_token: str
    expires_in: int
    account: AccountResponse
