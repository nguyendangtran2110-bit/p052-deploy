from enum import StrEnum


class ActorRole(StrEnum):
    ANONYMOUS = "anonymous"
    RESIDENT = "resident"
    MANAGEMENT = "management"
    SYSTEM = "system"


class AccountStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"


class ManagementRole(StrEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
