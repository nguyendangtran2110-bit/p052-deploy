from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateResidentCommand:
    resident_code: str
    full_name: str
    email: str | None = None
    phone: str | None = None


@dataclass(frozen=True, slots=True)
class CreateUnitCommand:
    project_code: str
    building: str
    floor: str | None
    unit_number: str
