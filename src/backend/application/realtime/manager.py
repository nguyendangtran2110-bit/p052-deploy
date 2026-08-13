from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.backend.infrastructure.db.models import Announcement, Conversation, Message, Ticket


@dataclass(slots=True)
class RealtimeSubscription:
    keys: frozenset[str]
    queue: asyncio.Queue[dict[str, Any]]


class ConnectionManager:
    """In-memory SSE fan-out for the single-process MVP deployment."""

    def __init__(self) -> None:
        self._connections: dict[str, set[asyncio.Queue[dict[str, Any]]]] = {}

    def subscribe(self, keys: set[str] | frozenset[str]) -> RealtimeSubscription:
        normalized = frozenset(key for key in keys if key)
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        for key in normalized:
            self._connections.setdefault(key, set()).add(queue)
        return RealtimeSubscription(keys=normalized, queue=queue)

    def unsubscribe(self, subscription: RealtimeSubscription) -> None:
        for key in subscription.keys:
            queues = self._connections.get(key)
            if queues is None:
                continue
            queues.discard(subscription.queue)
            if not queues:
                self._connections.pop(key, None)

    def publish(self, keys: set[str] | frozenset[str], event: str, data: dict[str, Any]) -> None:
        queues: set[asyncio.Queue[dict[str, Any]]] = set()
        for key in keys:
            queues.update(self._connections.get(key, set()))
        payload = {"event": event, "data": data}
        for queue in queues:
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                # A slow browser should not block the request that produced an event.
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                queue.put_nowait(payload)


realtime_manager = ConnectionManager()


def resident_realtime_key(resident_id: str | None) -> str | None:
    return f"resident:{resident_id}" if resident_id else None


def management_realtime_keys() -> set[str]:
    return {"management"}


def publish_message_event(
    message: Message,
    conversation: Conversation,
    *,
    include_management: bool = True,
    attachment_ids: list[str] | tuple[str, ...] | None = None,
) -> None:
    publish_message_payload(
        conversation,
        build_message_event(message, conversation, attachment_ids=attachment_ids),
        include_management=include_management,
    )


def build_message_event(
    message: Message,
    conversation: Conversation,
    *,
    attachment_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    ticket = conversation.__dict__.get("ticket")
    return {
        "id": message.id,
        "conversation_id": conversation.id,
        "ticket_id": ticket.id if ticket is not None else None,
        "role": message.role,
        "author_id": message.author_id,
        "content": message.content,
        "intent": message.intent,
        "citations": message.citations,
        "action_payload": message.action_payload,
        "workflow_id": message.workflow_id,
        "workflow_state": message.workflow_state,
        "workflow_version": message.workflow_version,
        "attachment_ids": list(attachment_ids)
            if attachment_ids is not None
            else [attachment.id for attachment in message.__dict__.get("attachments", [])],
        "created_at": _isoformat(message.created_at),
    }


def publish_message_payload(
    conversation: Conversation,
    data: dict[str, Any],
    *,
    include_management: bool = True,
) -> None:
    keys = _conversation_keys(conversation.resident_id, include_management=include_management)
    if keys:
        realtime_manager.publish(keys, "conversation.message.created", data)


def publish_conversation_event(
    conversation: Conversation,
    event: str,
    data: dict[str, Any],
    *,
    include_management: bool = True,
) -> None:
    keys = _conversation_keys(conversation.resident_id, include_management=include_management)
    if keys:
        realtime_manager.publish(keys, event, {"conversation_id": conversation.id, **data})


def publish_ticket_event(ticket: Ticket, event: str, data: dict[str, Any] | None = None) -> None:
    keys = _conversation_keys(ticket.resident_id, include_management=True)
    if keys:
        realtime_manager.publish(
            keys,
            event,
            {
                "ticket_id": ticket.id,
                "ticket_code": ticket.ticket_code,
                "conversation_id": ticket.conversation_id,
                "status": ticket.status,
                **(data or {}),
            },
        )


def publish_announcement_event(
    event: str,
    announcement: Announcement,
    *,
    resident_ids: list[str] | tuple[str, ...] | set[str] = (),
    include_management: bool = True,
    data: dict[str, Any] | None = None,
) -> None:
    keys = {key for resident_id in resident_ids if (key := resident_realtime_key(resident_id))}
    if include_management:
        keys.update(management_realtime_keys())
    if not keys:
        return
    payload = {
        "announcement_id": announcement.id,
        "announcement_code": announcement.announcement_code,
        "event": event,
        "status": announcement.status,
        "published_at": _isoformat(announcement.published_at) if announcement.published_at else None,
        **(data or {}),
    }
    realtime_manager.publish(keys, event, payload)


def _conversation_keys(resident_id: str | None, *, include_management: bool) -> set[str]:
    keys = {key for key in (resident_realtime_key(resident_id),) if key}
    if include_management:
        keys.update(management_realtime_keys())
    return keys


def _isoformat(value: datetime) -> str:
    return value.isoformat()
