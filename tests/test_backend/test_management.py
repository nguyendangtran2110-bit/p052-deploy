from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.asyncio
async def test_admin_manages_staff_and_ticket_assignment(client, admin_auth):
    staff_created = await client.post(
        "/api/v1/management/accounts",
        headers=admin_auth["headers"],
        json={
            "email": "staff@example.com",
            "password": "StaffPassword123!",
            "employee_code": "MGT-STAFF-001",
            "full_name": "Operations Staff",
            "department": "Maintenance",
            "management_role": "staff",
        },
    )
    staff_id = staff_created.json()["id"]
    staff_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "staff@example.com", "password": "StaffPassword123!"},
    )
    staff_headers = {"Authorization": f"Bearer {staff_login.json()['access_token']}"}

    accounts = await client.get("/api/v1/management/accounts", headers=admin_auth["headers"])
    forbidden_accounts = await client.get("/api/v1/management/accounts", headers=staff_headers)

    resident = await client.post(
        "/api/v1/residents",
        headers=admin_auth["headers"],
        json={
            "resident_code": "RES-MGT-001",
            "full_name": "Nguyen Hoang",
            "email": "hoang@example.com",
            "phone": "0900000088",
        },
    )
    unit = await client.post(
        "/api/v1/units",
        headers=admin_auth["headers"],
        json={"project_code": "ONB", "building": "A", "floor": "5", "unit_number": "A-0501"},
    )
    await client.post(
        f"/api/v1/residents/{resident.json()['id']}/units",
        headers=admin_auth["headers"],
        json={"unit_id": unit.json()["id"], "role": "owner", "is_primary": True},
    )
    resident_auth = await client.post(
        "/api/v1/auth/register/resident",
        json={
            "resident_code": "RES-MGT-001",
            "email": "hoang@example.com",
            "password": "ResidentPassword123!",
        },
    )
    ticket = await client.post(
        "/api/v1/tickets",
        headers={"Authorization": f"Bearer {resident_auth.json()['access_token']}"},
        json={
            "unit_id": unit.json()["id"],
            "category": "electrical",
            "priority": "high",
            "title": "Lobby light is not working",
            "description": "The lobby light on floor five has stopped working.",
            "location": "Building A, floor 5 lobby",
        },
    )
    due_at = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    assigned = await client.patch(
        f"/api/v1/management/tickets/{ticket.json()['id']}/assignment",
        headers=staff_headers,
        json={"assignee_account_id": staff_id, "due_at": due_at},
    )
    forbidden_reassignment = await client.patch(
        f"/api/v1/management/tickets/{ticket.json()['id']}/assignment",
        headers=staff_headers,
        json={"assignee_account_id": admin_auth["account"]["id"], "due_at": due_at},
    )
    dashboard = await client.get("/api/v1/management/dashboard", headers=staff_headers)
    disabled = await client.patch(
        f"/api/v1/management/accounts/{staff_id}",
        headers=admin_auth["headers"],
        json={"status": "disabled"},
    )
    disabled_access = await client.get("/api/v1/auth/me", headers=staff_headers)

    assert staff_created.status_code == 201
    assert accounts.status_code == 200
    assert accounts.json()["total"] == 2
    assert forbidden_accounts.status_code == 403
    assert assigned.status_code == 200
    assert assigned.json()["assigned_to_id"] == staff_id
    assert assigned.json()["events"][-1]["event_type"] == "ticket_assigned"
    assert forbidden_reassignment.status_code == 403
    assert dashboard.status_code == 200
    assert dashboard.json()["ticket_total"] == 1
    assert dashboard.json()["ticket_status_counts"]["submitted"] == 1
    assert disabled.status_code == 200
    assert disabled_access.status_code == 401
