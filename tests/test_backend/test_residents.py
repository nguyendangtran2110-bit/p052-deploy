import pytest


@pytest.mark.asyncio
async def test_management_can_bootstrap_resident_unit_and_form_ticket(client, management_headers):
    resident_response = await client.post(
        "/api/v1/residents",
        headers=management_headers,
        json={
            "resident_code": "RES-BOOTSTRAP",
            "full_name": "Le Minh",
            "email": "minh@example.com",
            "phone": "0900000022",
        },
    )
    unit_response = await client.post(
        "/api/v1/units",
        headers=management_headers,
        json={
            "project_code": "ONB",
            "building": "B",
            "floor": "8",
            "unit_number": "B-0808",
        },
    )
    resident_id = resident_response.json()["id"]
    unit_id = unit_response.json()["id"]
    linked = await client.post(
        f"/api/v1/residents/{resident_id}/units",
        headers=management_headers,
        json={"unit_id": unit_id, "role": "owner", "is_primary": True},
    )

    resident_headers = {"X-Actor-Role": "resident", "X-Resident-Id": resident_id}
    ticket = await client.post(
        "/api/v1/tickets",
        headers=resident_headers,
        json={
            "unit_id": unit_id,
            "category": "internet",
            "priority": "medium",
            "title": "Internet port is not active",
            "description": "The network port in the living room has no signal.",
            "location": "Unit B-0808, living room",
        },
    )
    profile = await client.get("/api/v1/residents/me", headers=resident_headers)

    assert resident_response.status_code == 201
    assert unit_response.status_code == 201
    assert linked.status_code == 200
    assert ticket.status_code == 201
    assert profile.json()["units"][0]["unit_number"] == "B-0808"
