import pytest

from src.backend.api.dependencies import get_agent_runtime
from src.main import app


class TicketAgent:
    def __init__(self, unit_id: str):
        self.unit_id = unit_id

    async def ainvoke(self, _state):
        return {
            "response": "I have collected the required information. Please confirm the ticket.",
            "intent": "create_ticket",
            "action": {
                "type": "create_ticket",
                "payload": {
                    "unit_id": self.unit_id,
                    "category": "electrical",
                    "priority": "high",
                    "title": "Hallway light is not working",
                    "description": "The hallway light outside the unit is not working.",
                    "location": "Floor 12, outside unit A-1204",
                },
            },
        }


class HandbookAgent:
    async def ainvoke(self, _state):
        return {
            "response": "The pool is open from 06:00 to 21:00.",
            "intent": "handbook_question",
            "citations": [
                {
                    "title": "Resident handbook",
                    "section": "Amenities - Swimming pool",
                    "page": 18,
                }
            ],
        }


@pytest.mark.asyncio
async def test_chat_flow_creates_ticket_through_same_backend(client, resident_unit, resident_headers):
    app.dependency_overrides[get_agent_runtime] = lambda: TicketAgent(resident_unit["unit_id"])
    try:
        response = await client.post(
            "/api/v1/chat/messages",
            json={
                "message": "Yes, create that ticket",
                "unit_id": resident_unit["unit_id"],
                "confirm_action": True,
                "idempotency_key": "chat-submit-001",
            },
            headers=resident_headers,
        )
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)

    assert response.status_code == 200
    data = response.json()
    assert data["action"]["type"] == "ticket_created"
    assert data["ticket"]["source"] == "chat"
    assert data["ticket"]["status"] == "submitted"
    assert data["ticket"]["events"][0]["event_type"] == "ticket_submitted"
    thread = await client.get(
        f"/api/v1/tickets/{data['ticket']['id']}/conversation",
        headers=resident_headers,
    )

    assert thread.status_code == 200
    assert thread.json()["conversation_id"] == data["ticket"]["conversation_id"]
    assert any(message["intent"] == "ticket_created" for message in thread.json()["messages"])


@pytest.mark.asyncio
async def test_anonymous_handbook_question_returns_citations(client):
    app.dependency_overrides[get_agent_runtime] = HandbookAgent
    try:
        response = await client.post(
            "/api/v1/chat/messages",
            json={"message": "What time does the pool close?"},
        )
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)

    assert response.status_code == 200
    assert response.json()["citations"][0]["page"] == 18
    assert "analysis" not in response.json()


class TicketContextAgent:
    def __init__(self):
        self.state = None

    async def ainvoke(self, state):
        self.state = state
        return {
            "response": "I can help with this ticket.",
            "intent": "ticket_question",
        }


class HandoffAgent:
    def __init__(self):
        self.state = None

    async def ainvoke(self, state):
        self.state = state
        return {
            "response": "I am handing this conversation to management for a follow-up.",
            "intent": "management_handoff",
            "action": {
                "type": "handoff_to_management",
                "payload": {"reason": "The question requires an operational decision."},
            },
        }


class ExplodingAgent:
    async def ainvoke(self, _state):
        raise AssertionError("The bot must not be invoked after management handoff")


class ResumedAgent:
    def __init__(self):
        self.calls = 0
        self.state = None

    async def ainvoke(self, state):
        self.calls += 1
        self.state = state
        return {
            "response": "The chatbot is active again and can help with this question.",
            "intent": "handbook_question",
        }


@pytest.mark.asyncio
async def test_resident_can_continue_ticket_conversation_with_ticket_context(
    client, resident_unit, resident_headers
):
    created = await client.post(
        "/api/v1/tickets",
        json={
            "unit_id": resident_unit["unit_id"],
            "category": "plumbing",
            "priority": "high",
            "title": "Water leak",
            "description": "Water is leaking under the kitchen sink.",
            "location": "Kitchen",
        },
        headers=resident_headers,
    )
    ticket_id = created.json()["id"]
    agent = TicketContextAgent()
    app.dependency_overrides[get_agent_runtime] = lambda: agent
    try:
        response = await client.post(
            f"/api/v1/tickets/{ticket_id}/messages",
            json={"message": "Has this ticket been assigned yet?"},
            headers=resident_headers,
        )
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)

    thread = await client.get(f"/api/v1/tickets/{ticket_id}/conversation", headers=resident_headers)

    assert response.status_code == 200
    assert response.json()["conversation_id"] == created.json()["conversation_id"]
    assert agent.state["metadata"]["ticket"]["id"] == ticket_id
    assert agent.state["metadata"]["ticket"]["status"] == "submitted"
    assert agent.state["metadata"]["messages"][-1]["content"] == "Has this ticket been assigned yet?"
    assert thread.status_code == 200
    assert [message["role"] for message in thread.json()["messages"]] == [
        "user",
        "system",
        "user",
        "assistant",
    ]


@pytest.mark.asyncio
async def test_management_handoff_keeps_resident_and_manager_in_one_conversation(
    client, resident_unit, resident_headers, management_headers
):
    handoff_agent = HandoffAgent()
    app.dependency_overrides[get_agent_runtime] = lambda: handoff_agent
    try:
        handoff = await client.post(
            "/api/v1/chat/messages",
            json={
                "message": "Tôi cần ban quản lý xác nhận một ngoại lệ trong nội quy.",
                "unit_id": resident_unit["unit_id"],
            },
            headers=resident_headers,
        )
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)

    conversation_id = handoff.json()["conversation_id"]
    queue = await client.get(
        "/api/v1/management/conversations/handoffs",
        headers=management_headers,
    )
    manager_reply = await client.post(
        f"/api/v1/management/conversations/{conversation_id}/messages",
        json={"message": "Ban quản lý đã kiểm tra và xác nhận trường hợp này."},
        headers=management_headers,
    )

    app.dependency_overrides[get_agent_runtime] = ExplodingAgent
    try:
        resident_follow_up = await client.post(
            "/api/v1/chat/messages",
            json={
                "message": "Cảm ơn, tôi muốn hỏi thêm một chi tiết.",
                "conversation_id": conversation_id,
            },
            headers=resident_headers,
        )
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)

    thread = await client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=resident_headers,
    )

    assert handoff.status_code == 200
    assert handoff.json()["action"]["type"] == "handoff_requested"
    assert queue.status_code == 200
    assert queue.json()["total"] == 1
    assert queue.json()["items"][0]["conversation_id"] == conversation_id
    assert manager_reply.status_code == 200
    assert manager_reply.json()["role"] == "management"
    assert manager_reply.json()["author_id"] == "manager-001"
    assert resident_follow_up.status_code == 200
    assert resident_follow_up.json()["action"]["type"] == "handoff_pending"
    assert thread.status_code == 200
    assert thread.json()["handoff_status"] == "management_active"
    assert [message["role"] for message in thread.json()["messages"]] == [
        "user",
        "assistant",
        "system",
        "management",
        "user",
        "system",
    ]


@pytest.mark.asyncio
async def test_management_can_return_conversation_to_chatbot(
    client, resident_unit, resident_headers, management_headers
):
    app.dependency_overrides[get_agent_runtime] = HandoffAgent
    try:
        handoff = await client.post(
            "/api/v1/chat/messages",
            json={
                "message": "Please ask management to review this exception.",
                "unit_id": resident_unit["unit_id"],
            },
            headers=resident_headers,
        )
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)

    conversation_id = handoff.json()["conversation_id"]
    manager_reply = await client.post(
        f"/api/v1/management/conversations/{conversation_id}/messages",
        json={"message": "Management has reviewed the context."},
        headers=management_headers,
    )
    resumed_agent = ResumedAgent()
    app.dependency_overrides[get_agent_runtime] = lambda: resumed_agent
    try:
        returned = await client.post(
            f"/api/v1/management/conversations/{conversation_id}/handoff-to-bot",
            json={"note": "The remaining question is covered by the handbook."},
            headers=management_headers,
        )
        resident_follow_up = await client.post(
            "/api/v1/chat/messages",
            json={
                "message": "What does the handbook say about the next step?",
                "conversation_id": conversation_id,
            },
            headers=resident_headers,
        )
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)

    thread = await client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=resident_headers,
    )

    assert manager_reply.status_code == 200
    assert returned.status_code == 200
    assert returned.json()["handoff_status"] == "bot_active"
    assert returned.json()["handoff_requested_at"] is None
    assert returned.json()["message"]["role"] == "system"
    assert returned.json()["message"]["intent"] == "management_handoff_to_bot"
    assert returned.json()["message"]["action_payload"] == {
        "from_status": "management_active",
        "to_status": "bot_active",
        "note": "The remaining question is covered by the handbook.",
    }
    assert resident_follow_up.status_code == 200
    assert resident_follow_up.json()["conversation_id"] == conversation_id
    assert resident_follow_up.json()["response"] == (
        "The chatbot is active again and can help with this question."
    )
    assert resumed_agent.calls == 1
    assert resumed_agent.state["metadata"]["handoff_status"] == "bot_active"
    assert thread.status_code == 200
    assert thread.json()["handoff_status"] == "bot_active"
    assert thread.json()["messages"][-1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_resident_cannot_return_conversation_to_chatbot(
    client, resident_unit, resident_headers, management_headers
):
    app.dependency_overrides[get_agent_runtime] = HandoffAgent
    try:
        handoff = await client.post(
            "/api/v1/chat/messages",
            json={
                "message": "Please ask management to review this exception.",
                "unit_id": resident_unit["unit_id"],
            },
            headers=resident_headers,
        )
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)

    conversation_id = handoff.json()["conversation_id"]
    returned = await client.post(
        f"/api/v1/management/conversations/{conversation_id}/handoff-to-bot",
        headers=resident_headers,
    )

    assert returned.status_code == 403


@pytest.mark.asyncio
async def test_only_one_manager_can_auto_assign_conversation(
    client, resident_unit, resident_headers, management_headers
):
    app.dependency_overrides[get_agent_runtime] = HandoffAgent
    try:
        handoff = await client.post(
            "/api/v1/chat/messages",
            json={
                "message": "Please ask management to review this exception.",
                "unit_id": resident_unit["unit_id"],
            },
            headers=resident_headers,
        )
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)

    conversation_id = handoff.json()["conversation_id"]
    first_manager_headers = {
        **management_headers,
        "X-Management-Role": "manager",
    }
    second_manager_headers = {
        "X-Actor-Role": "management",
        "X-Actor-Id": "manager-002",
        "X-Management-Role": "manager",
    }
    current = await client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=first_manager_headers,
    )
    first_reply = await client.post(
        f"/api/v1/management/conversations/{conversation_id}/messages",
        json={
            "message": "Manager one will handle this.",
            "conversation_version": current.json()["conversation_version"],
        },
        headers=first_manager_headers,
    )
    blocked = await client.post(
        f"/api/v1/management/conversations/{conversation_id}/messages",
        json={
            "message": "Manager two must reload or take over explicitly.",
            "conversation_version": current.json()["conversation_version"],
        },
        headers=second_manager_headers,
    )
    winner_reply = await client.post(
        f"/api/v1/management/conversations/{conversation_id}/messages",
        json={
            "message": "I will continue handling this conversation.",
            "conversation_version": first_reply.json()["conversation_version"],
        },
        headers=first_manager_headers,
    )
    stale_reply = await client.post(
        f"/api/v1/management/conversations/{conversation_id}/messages",
        json={
            "message": "This stale tab must reload first.",
            "conversation_version": first_reply.json()["conversation_version"],
        },
        headers=first_manager_headers,
    )

    assert current.status_code == 200
    assert first_reply.status_code == 200
    assert first_reply.json()["author_id"] == "manager-001"
    assert blocked.json()["error"]["code"] == "conflict"
    assert winner_reply.status_code == 200
    assert blocked.status_code == 409
    assert stale_reply.status_code == 409


@pytest.mark.asyncio
async def test_manager_can_explicitly_take_over_without_a_lease(
    client, resident_unit, resident_headers, management_headers
):
    app.dependency_overrides[get_agent_runtime] = HandoffAgent
    try:
        handoff = await client.post(
            "/api/v1/chat/messages",
            json={
                "message": "Please ask management to review this exception.",
                "unit_id": resident_unit["unit_id"],
            },
            headers=resident_headers,
        )
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)

    conversation_id = handoff.json()["conversation_id"]
    first_manager_headers = {**management_headers, "X-Management-Role": "manager"}
    second_manager_headers = {
        "X-Actor-Role": "management",
        "X-Actor-Id": "manager-002",
        "X-Management-Role": "manager",
    }
    conversation = await client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=first_manager_headers,
    )
    initial_reply = await client.post(
        f"/api/v1/management/conversations/{conversation_id}/messages",
        json={
            "message": "I am reviewing this request.",
            "conversation_version": conversation.json()["conversation_version"],
        },
        headers=first_manager_headers,
    )
    takeover = await client.post(
        f"/api/v1/management/conversations/{conversation_id}/takeover",
        json={
            "conversation_version": initial_reply.json()["conversation_version"],
            "note": "The original assignee is unavailable.",
        },
        headers=second_manager_headers,
    )

    assert conversation.status_code == 200
    assert initial_reply.status_code == 200
    assert takeover.status_code == 200
    assert takeover.json()["assigned_manager_id"] == "manager-002"
    assert takeover.json()["handoff_status"] == "management_active"
    assert takeover.json()["message"]["intent"] == "management_takeover"


@pytest.mark.asyncio
async def test_resident_can_list_normal_chat_history_without_ticket_conversations(
    client, resident_unit, resident_headers, management_headers
):
    app.dependency_overrides[get_agent_runtime] = HandbookAgent
    try:
        first = await client.post(
            "/api/v1/chat/messages",
            json={
                "message": "What time does the pool close?",
                "unit_id": resident_unit["unit_id"],
            },
            headers=resident_headers,
        )
        second = await client.post(
            "/api/v1/chat/messages",
            json={
                "message": "Are pets allowed in common areas?",
                "unit_id": resident_unit["unit_id"],
            },
            headers=resident_headers,
        )
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)

    ticket = await client.post(
        "/api/v1/tickets",
        json={
            "unit_id": resident_unit["unit_id"],
            "category": "plumbing",
            "priority": "medium",
            "title": "Leaking faucet",
            "description": "The kitchen faucet is leaking.",
            "location": "Kitchen",
        },
        headers=resident_headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert ticket.status_code == 201
    first_id = first.json()["conversation_id"]
    second_id = second.json()["conversation_id"]
    ticket_conversation_id = ticket.json()["conversation_id"]

    page = await client.get(
        "/api/v1/conversations?offset=0&limit=1",
        headers=resident_headers,
    )
    next_page = await client.get(
        "/api/v1/conversations?offset=1&limit=1",
        headers=resident_headers,
    )
    forbidden = await client.get(
        "/api/v1/conversations",
        headers=management_headers,
    )

    assert page.status_code == 200
    assert page.json()["total"] == 2
    assert len(page.json()["items"]) == 1
    assert page.json()["items"][0]["conversation_id"] == second_id
    assert page.json()["items"][0]["message_count"] == 2
    assert page.json()["items"][0]["last_message_preview"] == "The pool is open from 06:00 to 21:00."

    assert next_page.status_code == 200
    assert next_page.json()["items"][0]["conversation_id"] == first_id
    assert ticket_conversation_id not in {
        item["conversation_id"] for item in page.json()["items"] + next_page.json()["items"]
    }
    assert forbidden.status_code == 401
