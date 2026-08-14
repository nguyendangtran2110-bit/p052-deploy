from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """State schema cho LangGraph agent.

    Mỗi node đọc và ghi vào state này.
    total=False cho phép tất cả fields là optional.
    """

    query: str
    message: str
    actor_role: str
    actor_id: str
    resident_id: str | None
    conversation_id: str
    workflow_id: str | None
    workflow_type: str | None
    workflow_version: int | None
    confirmed_action_id: str | None
    confirm_action: bool
    selected_unit_id: str | None
    workflow_attachment_ids: list[str]
    messages: list[dict]
    workflow_draft: dict
    workflow_state: str | None
    pending_action: dict | None
    handbook_results: list[dict]
    context: str
    analysis: str
    response: str
    assistant_message: str
    intent: str
    draft: dict
    missing_fields: list[str]
    action: dict | None
    state: str | None
    citations: list[dict]
    attachment_ids: list[str]
    error_details: dict | None
    error: dict | None
    metadata: dict
