import pytest


def ticket_payload(unit_id: str) -> dict:
    return {
        "unit_id": unit_id,
        "category": "plumbing",
        "priority": "high",
        "title": "Water leak under kitchen sink",
        "description": "Water is leaking continuously under the kitchen sink.",
        "location": "Unit A-1204, kitchen",
    }


@pytest.mark.asyncio
async def test_form_flow_creates_ticket_with_audit_event(client, resident_unit, resident_headers):
    response = await client.post(
        "/api/v1/tickets",
        json=ticket_payload(resident_unit["unit_id"]),
        headers=resident_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["source"] == "form"
    assert data["status"] == "submitted"
    assert data["conversation_id"] is not None
    assert data["events"][0]["event_type"] == "ticket_submitted"
    thread = await client.get(f"/api/v1/tickets/{data['id']}/conversation", headers=resident_headers)

    assert thread.status_code == 200
    assert thread.json()["messages"][0]["intent"] == "ticket_submitted"
    assert thread.json()["messages"][1]["intent"] == "ticket_created"


@pytest.mark.asyncio
async def test_ticket_creation_is_idempotent(client, resident_unit, resident_headers):
    headers = {**resident_headers, "Idempotency-Key": "form-submit-001"}
    payload = ticket_payload(resident_unit["unit_id"])

    first = await client.post("/api/v1/tickets", json=payload, headers=headers)
    second = await client.post("/api/v1/tickets", json=payload, headers=headers)
    listed = await client.get("/api/v1/tickets", headers=resident_headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert listed.json()["total"] == 1


@pytest.mark.asyncio
async def test_management_can_approve_submitted_ticket(client, resident_unit, resident_headers, management_headers):
    created = await client.post(
        "/api/v1/tickets",
        json=ticket_payload(resident_unit["unit_id"]),
        headers=resident_headers,
    )
    ticket_id = created.json()["id"]

    approved = await client.patch(
        f"/api/v1/tickets/{ticket_id}/status",
        json={"status": "approved", "comment": "Request verified"},
        headers=management_headers,
    )

    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["events"][-1]["from_status"] == "submitted"
    assert approved.json()["events"][-1]["to_status"] == "approved"
    thread = await client.get(f"/api/v1/tickets/{ticket_id}/conversation", headers=resident_headers)

    assert thread.status_code == 200
    assert thread.json()["messages"][-1]["intent"] == "ticket_status_changed"
    assert thread.json()["messages"][-1]["action_payload"]["to_status"] == "approved"


@pytest.mark.asyncio
async def test_management_can_reply_inside_ticket_conversation(
    client, resident_unit, resident_headers, management_headers
):
    created = await client.post(
        "/api/v1/tickets",
        json=ticket_payload(resident_unit["unit_id"]),
        headers=resident_headers,
    )
    ticket_id = created.json()["id"]

    reply = await client.post(
        f"/api/v1/management/tickets/{ticket_id}/conversation/messages",
        json={"message": "Đội kỹ thuật sẽ kiểm tra căn hộ trong hôm nay."},
        headers=management_headers,
    )
    thread = await client.get(
        f"/api/v1/tickets/{ticket_id}/conversation",
        headers=resident_headers,
    )

    assert reply.status_code == 200
    assert reply.json()["role"] == "management"
    assert reply.json()["intent"] == "management_reply"
    assert thread.status_code == 200
    assert thread.json()["handoff_status"] == "management_active"
    assert thread.json()["messages"][-1]["content"] == "Đội kỹ thuật sẽ kiểm tra căn hộ trong hôm nay."


@pytest.mark.asyncio
async def test_resident_cannot_create_ticket_for_unlinked_unit(client, resident_headers):
    payload = ticket_payload("39e6ee33-ad4a-4db9-a077-2ae0f6ffb1cf")
    response = await client.post("/api/v1/tickets", json=payload, headers=resident_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


@pytest.mark.asyncio
async def test_management_can_return_ticket_conversation_to_chatbot(
    client, resident_unit, resident_headers, management_headers
):
    created = await client.post(
        "/api/v1/tickets",
        json=ticket_payload(resident_unit["unit_id"]),
        headers=resident_headers,
    )
    ticket_id = created.json()["id"]

    await client.post(
        f"/api/v1/management/tickets/{ticket_id}/conversation/messages",
        json={"message": "The management team reviewed this ticket."},
        headers=management_headers,
    )
    returned = await client.post(
        f"/api/v1/management/tickets/{ticket_id}/conversation/handoff-to-bot",
        json={"note": "The resident can continue with handbook guidance."},
        headers=management_headers,
    )
    thread = await client.get(
        f"/api/v1/tickets/{ticket_id}/conversation",
        headers=resident_headers,
    )

    assert returned.status_code == 200
    assert returned.json()["handoff_status"] == "bot_active"
    assert returned.json()["message"]["intent"] == "management_handoff_to_bot"
    assert thread.status_code == 200
    assert thread.json()["handoff_status"] == "bot_active"
