from dataclasses import dataclass

from src.backend.domain.identity.enums import ActorRole, ManagementRole


@dataclass(frozen=True, slots=True)
class ActorContext:
    role: ActorRole
    actor_id: str | None = None
    resident_id: str | None = None
    management_role: ManagementRole | None = None

    @property
    def is_management(self) -> bool:
        return self.role in {ActorRole.MANAGEMENT, ActorRole.SYSTEM}

    @property
    def is_authenticated(self) -> bool:
        return self.role is not ActorRole.ANONYMOUS

    @property
    def is_management_admin(self) -> bool:
        return self.is_management and self.management_role is ManagementRole.ADMIN
