import pytest


@pytest.mark.asyncio
async def test_chat_incident_creates_a_profile_prefilled_draft(client):
    response = await client.post(
        "/api/v1/chat/query",
        json={"message": "NƯỚC đang rò dưới bồn rửa bếp", "actor_role": "resident"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["notification"]["kind"] == "ticket_draft_available"
    assert payload["draft_preview"]["location"] == "Tower A · Floor 12 · Unit 12B · Kitchen"


@pytest.mark.asyncio
async def test_manager_cannot_submit_resident_draft(client):
    created = await client.post(
        "/api/v1/ticket-drafts",
        json={"message": "Điện căn 12B bị mất", "actor_role": "resident"},
    )
    draft_id = created.json()["id"]
    response = await client.post(f"/api/v1/ticket-drafts/{draft_id}/submit", json={"actor_role": "manager"})
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_resolution_requires_a_note(client):
    created = await client.post("/api/v1/ticket-drafts", json={"message": "Hỏng khóa cửa căn 12B", "actor_role": "resident"})
    submitted = await client.post(f"/api/v1/ticket-drafts/{created.json()['id']}/submit", json={"actor_role": "resident"})
    ticket_id = submitted.json()["ticket"]["id"]
    await client.patch(f"/api/v1/tickets/{ticket_id}", json={"actor_role": "manager", "status": "APPROVED"})
    await client.patch(f"/api/v1/tickets/{ticket_id}", json={"actor_role": "manager", "status": "IN_PROGRESS"})
    response = await client.patch(f"/api/v1/tickets/{ticket_id}", json={"actor_role": "manager", "status": "RESOLVED"})
    assert response.status_code == 422
