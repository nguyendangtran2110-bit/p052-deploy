from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.application.auth.service import AuthService
from src.backend.application.chat.contracts import AgentRuntime
from src.backend.core.config import Settings, get_settings
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import AuthenticationError, AuthorizationError
from src.backend.domain.identity.enums import ActorRole, ManagementRole
from src.backend.infrastructure.db.session import get_db_session

bearer_scheme = HTTPBearer(auto_error=False, description="JWT access token")


def get_agent_runtime() -> AgentRuntime:
    from src.agents.graph import agent

    return agent


async def get_actor_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    x_actor_role: Annotated[str | None, Header(alias="X-Actor-Role")] = None,
    x_actor_id: Annotated[str | None, Header(alias="X-Actor-Id")] = None,
    x_resident_id: Annotated[str | None, Header(alias="X-Resident-Id")] = None,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ActorContext:
    if credentials is not None:
        if credentials.scheme.lower() != "bearer":
            raise AuthenticationError("Bearer authentication is required")
        return await AuthService(session, settings).authenticate_access_token(credentials.credentials)

    if not settings.dev_auth_enabled:
        return ActorContext(role=ActorRole.ANONYMOUS)

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
        return ActorContext(
            role=role,
            actor_id=x_actor_id or "local-management",
            management_role=ManagementRole.ADMIN,
        )

    return ActorContext(role=ActorRole.ANONYMOUS)


def require_resident(actor: ActorContext = Depends(get_actor_context)) -> ActorContext:
    if actor.role is not ActorRole.RESIDENT:
        raise AuthenticationError("Resident authentication is required")
    return actor


def require_management(actor: ActorContext = Depends(get_actor_context)) -> ActorContext:
    if not actor.is_management:
        raise AuthorizationError("Management permission is required")
    return actor


def require_management_admin(actor: ActorContext = Depends(get_actor_context)) -> ActorContext:
    if not actor.is_management_admin:
        raise AuthorizationError("Management administrator permission is required")
    return actor


def require_authenticated(actor: ActorContext = Depends(get_actor_context)) -> ActorContext:
    if not actor.is_authenticated:
        raise AuthenticationError("Authentication is required")
    return actor
