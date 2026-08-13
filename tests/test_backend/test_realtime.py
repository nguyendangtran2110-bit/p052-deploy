import asyncio

import pytest

from src.backend.application.realtime.manager import ConnectionManager


@pytest.mark.asyncio
async def test_realtime_manager_fans_out_to_matching_subscribers_only():
    manager = ConnectionManager()
    resident_subscription = manager.subscribe({"resident:resident-1"})
    management_subscription = manager.subscribe({"management"})

    manager.publish({"resident:resident-1"}, "ticket.status.changed", {"ticket_id": "ticket-1"})

    resident_event = await asyncio.wait_for(resident_subscription.queue.get(), timeout=0.1)
    assert resident_event["event"] == "ticket.status.changed"
    assert resident_event["data"]["ticket_id"] == "ticket-1"
    assert management_subscription.queue.empty()

    manager.publish({"management"}, "conversation.message.created", {"conversation_id": "conversation-1"})
    management_event = await asyncio.wait_for(management_subscription.queue.get(), timeout=0.1)
    assert management_event["event"] == "conversation.message.created"

    manager.unsubscribe(resident_subscription)
    manager.unsubscribe(management_subscription)


@pytest.mark.asyncio
async def test_realtime_stream_requires_authentication(client):
    response = await client.get("/api/v1/realtime/stream")

    assert response.status_code == 401
