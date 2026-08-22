from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """State schema cho LangGraph agent và RAG subgraph.

    Mỗi node đọc và ghi vào state này.
    total=False cho phép tất cả fields là optional.
    """

    # Input & Actors
    query: str
    message: str
    actor_role: str
    actor_id: str
    resident_id: str | None
    conversation_id: str
    selected_unit_id: str | None

    # Workflows & Drafting
    workflow_id: str | None
    workflow_type: str | None
    workflow_version: int | None
    workflow_state: str | None
    workflow_draft: dict
    workflow_attachment_ids: list[str]
    confirmed_action_id: str | None
    confirm_action: bool
    pending_action: dict | None

    # Messages & History
    messages: list[dict]
    chat_history: list[dict]

    # Context & Retrieval
    handbook_results: list[dict]
    retrieved_chunks: list[dict]
    rag_response: dict
    context: str

    # Outputs & Intent
    intent: str
    draft: dict
    missing_fields: list[str]
    action: dict | None
    state: str | None
    response: str
    assistant_message: str
    analysis: str
    citations: list[dict]
    attachment_ids: list[str]

    # Errors & Metadata
    error_details: dict | None
    error: dict | str | None
    metadata: dict
