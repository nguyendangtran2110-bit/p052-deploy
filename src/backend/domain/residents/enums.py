from enum import StrEnum


class ResidentUnitRole(StrEnum):
    OWNER = "owner"
    TENANT = "tenant"
    FAMILY = "family"
