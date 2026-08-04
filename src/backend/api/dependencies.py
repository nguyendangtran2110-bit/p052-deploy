from typing import Annotated

from fastapi import Depends, Header

from src.backend.application.chat.contracts import AgentRuntime
from src.backend.core.config import Settings, get_settings
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import AuthenticationError, AuthorizationError
from src.backend.domain.identity.enums import ActorRole


def get_agent_runtime() -> AgentRuntime:
    from src.agents.graph import agent

    return agent


def get_actor_context(
    x_actor_role: Annotated[str | None, Header(alias="X-Actor-Role")] = None,
    x_actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    x_resident_id: Annotated[str | None, Header(alias="X-Resident-Id")] = None,
    settings: Settings = Depends(get_settings),
) -> ActorContext:
    if x_actor_role is None:
        role = ActorRole.RESIDENT if x_resident_id else ActorRole.ANONYMOUS
    else:
        try:
            role = ActorRole(x_actor_role.lower())
        except ValueError as exc:
            raise AuthenticationError("X-Actor-Role is invalid") from exc

    if role is ActorRole.RESIDENT:
        if not x_resident_id:
            raise AuthenticationError("X-Resident-Id is required for resident requests")
        return ActorContext(role=role, actor_id=x_actor_id or x_resident_id, resident_id=x_resident_id)

    if role is ActorRole.MANAGEMENT:
        if not x_actor_id and not settings.dev_auth_enabled:
            raise AuthenticationError("X-Actor-Id is required for management requests")
        return ActorContext(role=role, actor_id=x_actor_id or "local-management")

    return ActorContext(role=ActorRole.ANONYMOUS)


def require_resident(actor: ActorContext = Depends(get_actor_context)) -> ActorContext:
    if actor.role is not ActorRole.RESIDENT:
        raise AuthenticationError("Resident authentication is required")
    return actor


def require_management(actor: ActorContext = Depends(get_actor_context)) -> ActorContext:
    if not actor.is_management:
        raise AuthorizationError("Management permission is required")
    return actor
