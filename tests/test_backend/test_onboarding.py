import pytest


@pytest.mark.asyncio
async def test_resident_can_track_onboarding_tasks_and_information(
    client, resident_unit, resident_headers, management_headers
):
    initial = await client.get("/api/v1/onboarding", headers=resident_headers)

    assert initial.status_code == 200
    checklist = initial.json()["items"][0]
    assert checklist["unit_id"] == resident_unit["unit_id"]
    assert checklist["progress_percent"] == 0
    assert checklist["required_item_count"] == len(checklist["items"])

    task = next(item for item in checklist["items"] if item["item_type"] == "task")
    information = next(item for item in checklist["items"] if item["item_type"] == "information")

    completed = await client.patch(
        f"/api/v1/onboarding/items/{task['id']}",
        headers=resident_headers,
        json={"status": "completed"},
    )
    read = await client.patch(
        f"/api/v1/onboarding/items/{information['id']}",
        headers=resident_headers,
        json={"status": "read"},
    )
    invalid = await client.patch(
        f"/api/v1/onboarding/items/{information['id']}",
        headers=resident_headers,
        json={"status": "completed"},
    )
    updated = await client.get("/api/v1/onboarding", headers=resident_headers)

    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert read.status_code == 200
    assert read.json()["status"] == "read"
    assert invalid.status_code == 422
    assert updated.json()["items"][0]["completed_item_count"] == 2
    assert updated.json()["items"][0]["progress_percent"] > 0

    management = await client.get("/api/v1/management/onboarding", headers=management_headers)
    detail = await client.get(
        f"/api/v1/management/onboarding/{resident_unit['resident_id']}",
        headers=management_headers,
    )
    forbidden = await client.get("/api/v1/onboarding", headers=management_headers)

    assert management.status_code == 200
    assert management.json()["total"] == 1
    assert management.json()["items"][0]["resident_id"] == resident_unit["resident_id"]
    assert management.json()["items"][0]["completed_item_count"] == 2
    assert detail.status_code == 200
    assert detail.json()["items"][0]["resident_name"] == "Nguyen Van An"
    assert forbidden.status_code == 401


@pytest.mark.asyncio
async def test_management_can_filter_onboarding_progress(client, resident_unit, management_headers):
    response = await client.get(
        "/api/v1/management/onboarding?search=RES-001&project_code=ONB&building=A&is_completed=false",
        headers=management_headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["unit"]["unit_number"] == "A-1204"
