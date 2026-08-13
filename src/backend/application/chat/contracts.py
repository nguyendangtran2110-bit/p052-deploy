from dataclasses import dataclass, field
from typing import Any, Protocol


class AgentRuntime(Protocol):
    async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class ChatCommand:
    message: str
    conversation_id: str | None = None
    ticket_id: str | None = None
    unit_id: str | None = None
    confirm_action: bool = False
    workflow_id: str | None = None
    workflow_version: int | None = None
    confirmed_action_id: str | None = None
    idempotency_key: str | None = None
    attachment_ids: tuple[str, ...] = ()


@dataclass(slots=True)
class ChatOutcome:
    conversation_id: str
    response: str
    citations: list[dict[str, Any]] = field(default_factory=list)
    action: dict[str, Any] | None = None
    ticket: Any | None = None
    announcement: Any | None = None
    workflow_id: str | None = None
    workflow_type: str | None = None
    state: str | None = None
    workflow_version: int | None = None
    draft: dict[str, Any] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    message: Any | None = None
