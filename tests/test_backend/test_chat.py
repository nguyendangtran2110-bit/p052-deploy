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
