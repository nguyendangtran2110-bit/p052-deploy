from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TypedDict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

WorkflowType = Literal["resident_ticket", "manager_announcement"]
ActorRole = Literal["resident", "management"]


class AgentInput(TypedDict, total=False):
    query: str
    message: str
    actor_role: ActorRole | str
    actor_id: str
    resident_id: str | None
    conversation_id: str
    workflow_id: str | None
    workflow_type: WorkflowType | str | None
    workflow_version: int | None
    confirmed_action_id: str | None
    confirm_action: bool
    selected_unit_id: str | None
    attachment_ids: list[str]
    workflow_attachment_ids: list[str]
    messages: list[dict[str, Any]]
    workflow_draft: dict[str, Any] | None
    workflow_state: str | None
    pending_action: dict[str, Any] | None
    handbook_results: list[dict[str, Any]]
    metadata: dict[str, Any]


class TicketDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    unit_id: UUID | None = None
    category: str | None = Field(default=None, min_length=1, max_length=100)
    priority: Literal["low", "medium", "high", "urgent"] | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=50000)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=10)


class AnnouncementScopeDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scope_type: Literal["all_residents", "project", "building", "unit"]
    project_code: str | None = Field(default=None, max_length=50)
    building: str | None = Field(default=None, max_length=100)
    unit_id: UUID | None = None


class AnnouncementDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str | None = Field(default=None, min_length=2, max_length=255)
    content: str | None = Field(default=None, min_length=2, max_length=50000)
    type: Literal[
        "general",
        "maintenance",
        "facility",
        "regulation_update",
        "event",
        "emergency",
    ] = "general"
    priority: Literal["normal", "important", "urgent"] = "normal"
    expires_at: datetime | None = None
    scopes: list[AnnouncementScopeDraft] = Field(default_factory=list)
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=10)


class AgentAction(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str = Field(min_length=1, max_length=80)
    action_id: UUID | None = None
    requires_confirmation: bool | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentStructuredResult(BaseModel):
    """Strict LLM boundary; backend enriches identity fields from trusted state."""

    model_config = ConfigDict(extra="ignore")

    intent: str = "handbook_question"
    assistant_message: str = Field(
        description="A concise, user-facing response in the user's language. Must not be empty."
    )
    draft: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    action: AgentAction | None = None
    attachment_ids: list[UUID] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    error: dict[str, Any] | None = None


class AgentResult(TypedDict, total=False):
    workflow_id: str | None
    workflow_type: str | None
    state: str | None
    workflow_version: int | None
    intent: str
    assistant_message: str
    response: str
    draft: dict[str, Any]
    missing_fields: list[str]
    action: dict[str, Any] | None
    attachment_ids: list[str]
    citations: list[dict[str, Any]]
    error: dict[str, Any] | None
