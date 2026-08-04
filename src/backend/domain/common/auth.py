from dataclasses import dataclass

from src.backend.domain.identity.enums import ActorRole


@dataclass(frozen=True, slots=True)
class ActorContext:
    role: ActorRole
    actor_id: str | None = None
    resident_id: str | None = None

    @property
    def is_management(self) -> bool:
        return self.role in {ActorRole.MANAGEMENT, ActorRole.SYSTEM}

    @property
    def is_authenticated(self) -> bool:
        return self.role is not ActorRole.ANONYMOUS
