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


@pytest.mark.asyncio
async def test_manager_deletes_resident_account_and_admin_deletes_manager_account(client, admin_auth):
    manager_created = await client.post(
        "/api/v1/management/accounts",
        headers=admin_auth["headers"],
        json={
            "email": "manager@example.com",
            "password": "ManagerPassword123!",
            "employee_code": "MGT-MANAGER-001",
            "full_name": "Building Manager",
            "management_role": "manager",
        },
    )
    manager_id = manager_created.json()["id"]
    manager_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "manager@example.com", "password": "ManagerPassword123!"},
    )
    manager_headers = {"Authorization": f"Bearer {manager_login.json()['access_token']}"}

    resident = await client.post(
        "/api/v1/residents",
        headers=admin_auth["headers"],
        json={
            "resident_code": "RES-DELETE-001",
            "full_name": "Resident To Delete",
            "email": "delete-resident@example.com",
            "phone": "0900000099",
        },
    )
    resident_id = resident.json()["id"]
    resident_auth = await client.post(
        "/api/v1/auth/register/resident",
        json={
            "resident_code": "RES-DELETE-001",
            "email": "delete-resident@example.com",
            "password": "ResidentPassword123!",
        },
    )
    resident_headers = {"Authorization": f"Bearer {resident_auth.json()['access_token']}"}

    resident_list = await client.get("/api/v1/management/residents", headers=manager_headers)
    resident_detail = await client.get(f"/api/v1/management/residents/{resident_id}", headers=manager_headers)
    manager_delete_management = await client.delete(
        f"/api/v1/management/accounts/{manager_id}",
        headers=manager_headers,
    )
    delete_resident_account = await client.delete(
        f"/api/v1/management/residents/{resident_id}/account",
        headers=manager_headers,
    )
    deleted_resident_access = await client.get("/api/v1/auth/me", headers=resident_headers)
    resident_without_account = await client.get(
        f"/api/v1/management/residents/{resident_id}", headers=manager_headers
    )
    dashboard = await client.get("/api/v1/management/dashboard", headers=manager_headers)
    admin_delete_self = await client.delete(
        f"/api/v1/management/accounts/{admin_auth['account']['id']}",
        headers=admin_auth["headers"],
    )
    admin_delete_manager = await client.delete(
        f"/api/v1/management/accounts/{manager_id}",
        headers=admin_auth["headers"],
    )
    deleted_manager_access = await client.get("/api/v1/auth/me", headers=manager_headers)

    assert manager_created.status_code == 201
    assert resident.status_code == 201
    assert resident_auth.status_code == 201
    assert resident_list.status_code == 200
    assert resident_list.json()["total"] == 1
    assert resident_list.json()["items"][0]["account"]["email"] == "delete-resident@example.com"
    assert resident_detail.status_code == 200
    assert resident_detail.json()["units"] == []
    assert manager_delete_management.status_code == 403
    assert delete_resident_account.status_code == 204
    assert deleted_resident_access.status_code == 401
    assert resident_without_account.status_code == 200
    assert resident_without_account.json()["account"] is None
    assert dashboard.status_code == 200
    assert dashboard.json()["active_residents"] == 1
    assert admin_delete_self.status_code == 409
    assert admin_delete_manager.status_code == 204
    assert deleted_manager_access.status_code == 401


@pytest.mark.asyncio
async def test_management_searches_and_updates_resident_profile(client, admin_auth):
    first = await client.post(
        "/api/v1/residents",
        headers=admin_auth["headers"],
        json={
            "resident_code": "RES-SEARCH-001",
            "full_name": "Tran Thi Mot",
            "email": "search-one@example.com",
            "phone": "0900000011",
        },
    )
    second = await client.post(
        "/api/v1/residents",
        headers=admin_auth["headers"],
        json={
            "resident_code": "RES-SEARCH-002",
            "full_name": "Tran Thi Hai",
            "email": "search-two@example.com",
            "phone": "0900000012",
        },
    )
    first_id = first.json()["id"]

    search_by_code = await client.get(
        "/api/v1/management/residents",
        params={"search": "RES-SEARCH-002"},
        headers=admin_auth["headers"],
    )
    update = await client.patch(
        f"/api/v1/management/residents/{first_id}",
        headers=admin_auth["headers"],
        json={
            "full_name": "Tran Thi Mot Updated",
            "phone": "0900000091",
            "is_active": False,
        },
    )
    search_by_updated_name = await client.get(
        "/api/v1/management/residents",
        params={"search": "Updated"},
        headers=admin_auth["headers"],
    )
    search_inactive = await client.get(
        "/api/v1/management/residents",
        params={"is_active": "false"},
        headers=admin_auth["headers"],
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert search_by_code.status_code == 200
    assert search_by_code.json()["total"] == 1
    assert search_by_code.json()["items"][0]["resident_code"] == "RES-SEARCH-002"
    assert update.status_code == 200
    assert update.json()["full_name"] == "Tran Thi Mot Updated"
    assert update.json()["phone"] == "0900000091"
    assert update.json()["is_active"] is False
    assert search_by_updated_name.json()["total"] == 1
    assert search_by_updated_name.json()["items"][0]["id"] == first_id
    assert search_inactive.json()["total"] == 1
    assert search_inactive.json()["items"][0]["id"] == first_id
