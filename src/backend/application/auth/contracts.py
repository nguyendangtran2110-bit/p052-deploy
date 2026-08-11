from dataclasses import dataclass
from typing import Any

from src.backend.domain.identity.enums import ManagementRole


@dataclass(frozen=True, slots=True)
class ClientContext:
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass(frozen=True, slots=True)
class ResidentRegistrationCommand:
    resident_code: str
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class ManagementRegistrationCommand:
    email: str
    password: str
    employee_code: str
    full_name: str
    management_role: ManagementRole = ManagementRole.MANAGER
    phone: str | None = None
    department: str | None = None
    job_title: str | None = None
    project_code: str | None = None
    building: str | None = None


@dataclass(frozen=True, slots=True)
class AuthResult:
    account: Any
    access_token: str
    refresh_token: str
    expires_in: int


@dataclass(frozen=True, slots=True)
class PasswordResetRequestResult:
    email: str
    raw_token: str


@dataclass(frozen=True, slots=True)
class EmailVerificationRequestResult:
    email: str
    raw_code: str
