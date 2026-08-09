from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, StringConstraints

from src.backend.domain.identity.enums import AccountStatus, ManagementRole

Password = Annotated[str, StringConstraints(min_length=12, max_length=128)]


class ManagementAccountCreateRequest(BaseModel):
    email: EmailStr
    password: Password
    employee_code: str = Field(min_length=2, max_length=50)
    full_name: str = Field(min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    department: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=100)
    management_role: ManagementRole = ManagementRole.STAFF
    project_code: str | None = Field(default=None, max_length=50)
    building: str | None = Field(default=None, max_length=100)


class ManagementAccountUpdateRequest(BaseModel):
    email: EmailStr | None = None
    status: AccountStatus | None = None
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    department: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=100)
    management_role: ManagementRole | None = None
    project_code: str | None = Field(default=None, max_length=50)
    building: str | None = Field(default=None, max_length=100)


class ManagementResidentUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=8, max_length=30)
    is_active: bool | None = None


class TicketAssignmentRequest(BaseModel):
    assignee_account_id: UUID | None
    due_at: datetime | None = None
