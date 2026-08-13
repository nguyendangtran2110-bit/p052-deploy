from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class WorkflowAgentResult:
    response: str
    intent: str | None
    draft: dict[str, Any] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    action: dict[str, Any] | None = None
    citations: list[dict[str, Any]] = field(default_factory=list)
    attachment_ids: list[str] = field(default_factory=list)
    error: dict[str, Any] | None = None


@dataclass(slots=True)
class WorkflowOutcome:
    workflow: Any
    conversation: Any
    assistant_message: Any
    action: dict[str, Any] | None
    ticket: Any | None = None
    announcement: Any | None = None
    citations: list[dict[str, Any]] = field(default_factory=list)
