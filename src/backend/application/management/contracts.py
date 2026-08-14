from dataclasses import dataclass, field

from src.backend.domain.identity.enums import AccountStatus, ManagementRole


@dataclass(frozen=True, slots=True)
class UpdateManagementAccountCommand:
    changed_fields: frozenset[str] = field(default_factory=frozenset)
    email: str | None = None
    status: AccountStatus | None = None
    full_name: str | None = None
    phone: str | None = None
    department: str | None = None
    job_title: str | None = None
    management_role: ManagementRole | None = None
    project_code: str | None = None
    building: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateResidentCommand:
    changed_fields: frozenset[str] = field(default_factory=frozenset)
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    is_active: bool | None = None
