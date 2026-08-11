import asyncio
from unittest.mock import AsyncMock

import pytest

from src.backend.api.dependencies import get_settings
from src.backend.application.realtime import realtime_manager
from src.backend.core.config import Settings
from src.backend.infrastructure.storage import S3Storage
from src.main import app


def announcement_payload(*, building: str = "A") -> dict:
    return {
        "title": "Elevator maintenance",
        "content": "The elevator will be serviced tomorrow morning.",
        "type": "maintenance",
        "priority": "important",
        "scopes": [{"scope_type": "building", "building": building, "project_code": "ONB"}],
    }


@pytest.mark.asyncio
async def test_announcement_publish_visibility_read_and_statistics(
    client, resident_unit, resident_headers, management_headers
):
    created = await client.post(
        "/api/v1/management/announcements",
        json=announcement_payload(),
        headers=management_headers,
    )
    assert created.status_code == 201, created.text
    draft = created.json()
    assert draft["status"] == "draft"
    assert draft["version"] == 0
    assert draft["events"][0]["event_type"] == "created"

    edited = await client.patch(
        f"/api/v1/management/announcements/{draft['id']}",
        json={"version": 0, "title": "Elevator maintenance updated"},
        headers=management_headers,
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["version"] == 1

    before_publish = await client.get("/api/v1/announcements", headers=resident_headers)
    assert before_publish.status_code == 200
    assert before_publish.json()["total"] == 0

    published = await client.post(
        f"/api/v1/management/announcements/{draft['id']}/publish",
        json={"version": 1},
        headers=management_headers,
    )
    assert published.status_code == 200, published.text
    assert published.json()["status"] == "published"
    assert published.json()["version"] == 2
    assert any(event["event_type"] == "published" for event in published.json()["events"])

    listed = await client.get("/api/v1/announcements", headers=resident_headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["is_read"] is False
    assert (await client.get("/api/v1/announcements/unread-count", headers=resident_headers)).json() == {
        "unread_count": 1
    }

    detail = await client.get(f"/api/v1/announcements/{draft['id']}", headers=resident_headers)
    assert detail.status_code == 200
    assert detail.json()["is_read"] is True
    assert (await client.get("/api/v1/announcements/unread-count", headers=resident_headers)).json() == {
        "unread_count": 0
    }

    read_again = await client.post(f"/api/v1/announcements/{draft['id']}/read", headers=resident_headers)
    assert read_again.status_code == 200

    statistics = await client.get(
        f"/api/v1/management/announcements/{draft['id']}/statistics",
        headers=management_headers,
    )
    assert statistics.status_code == 200
    assert statistics.json() == {
        "announcement_id": draft["id"],
        "eligible_resident_count": 1,
        "read_count": 1,
        "unread_count": 0,
    }


@pytest.mark.asyncio
async def test_announcement_audience_and_management_workflow(client, resident_unit, resident_headers, management_headers):
    outside = await client.post(
        "/api/v1/management/announcements",
        json=announcement_payload(building="B"),
        headers=management_headers,
    )
    assert outside.status_code == 201
    outside_id = outside.json()["id"]
    published = await client.post(
        f"/api/v1/management/announcements/{outside_id}/publish",
        json={"version": 0},
        headers=management_headers,
    )
    assert published.status_code == 200

    resident_items = await client.get("/api/v1/announcements", headers=resident_headers)
    assert resident_items.status_code == 200
    assert resident_items.json()["total"] == 0
    hidden_detail = await client.get(f"/api/v1/announcements/{outside_id}", headers=resident_headers)
    assert hidden_detail.status_code == 404

    stale_update = await client.patch(
        f"/api/v1/management/announcements/{outside_id}",
        json={"version": 0, "title": "Stale edit"},
        headers=management_headers,
    )
    assert stale_update.status_code == 409

    cannot_delete = await client.delete(
        f"/api/v1/management/announcements/{outside_id}", headers=management_headers
    )
    assert cannot_delete.status_code == 409

    draft = await client.post(
        "/api/v1/management/announcements",
        json={"title": "Draft", "content": "Draft content", "scopes": []},
        headers=management_headers,
    )
    assert draft.status_code == 201
    deleted = await client.delete(
        f"/api/v1/management/announcements/{draft.json()['id']}", headers=management_headers
    )
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_announcement_sse_targets_matching_resident(client, resident_unit, resident_headers, management_headers):
    subscription = realtime_manager.subscribe({f"resident:{resident_unit['resident_id']}"})
    try:
        created = await client.post(
            "/api/v1/management/announcements",
            json=announcement_payload(),
            headers=management_headers,
        )
        assert created.status_code == 201
        published = await client.post(
            f"/api/v1/management/announcements/{created.json()['id']}/publish",
            json={"version": 0},
            headers=management_headers,
        )
        assert published.status_code == 200
        event = await asyncio.wait_for(subscription.queue.get(), timeout=0.1)
        assert event["event"] == "announcement.published"
        assert event["data"]["announcement_id"] == created.json()["id"]
        assert "content" not in event["data"]
    finally:
        realtime_manager.unsubscribe(subscription)


@pytest.mark.asyncio
async def test_staff_cannot_manage_announcements(client):
    response = await client.post(
        "/api/v1/management/announcements",
        json=announcement_payload(),
        headers={
            "X-Actor-Role": "management",
            "X-Actor-Id": "staff-001",
            "X-Management-Role": "staff",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_announcement_attachment_uses_existing_s3_flow(
    client, resident_unit, resident_headers, management_headers, monkeypatch
):
    settings = Settings(aws_s3_bucket_name="test-private-bucket", aws_region="ap-southeast-1")
    app.dependency_overrides[get_settings] = lambda: settings
    upload = AsyncMock(return_value="https://s3.test/upload")
    download = AsyncMock(return_value="https://s3.test/download")
    monkeypatch.setattr(S3Storage, "create_presigned_upload", upload)
    monkeypatch.setattr(S3Storage, "create_presigned_download", download)
    try:
        presigned = await client.post(
            "/api/v1/attachments/presign",
            headers=management_headers,
            json={"filename": "notice.pdf", "content_type": "application/pdf", "size_bytes": 2048},
        )
        assert presigned.status_code == 201
        attachment_id = presigned.json()["id"]

        created = await client.post(
            "/api/v1/management/announcements",
            headers=management_headers,
            json={**announcement_payload(), "attachment_ids": [attachment_id]},
        )
        assert created.status_code == 201, created.text
        assert created.json()["attachments"][0]["id"] == attachment_id

        published = await client.post(
            f"/api/v1/management/announcements/{created.json()['id']}/publish",
            json={"version": 0},
            headers=management_headers,
        )
        assert published.status_code == 200
        downloaded = await client.get(
            f"/api/v1/attachments/{attachment_id}/download", headers=resident_headers
        )
        assert downloaded.status_code == 200
        assert downloaded.json()["download_url"] == "https://s3.test/download"
    finally:
        app.dependency_overrides.pop(get_settings, None)


@pytest.mark.asyncio
async def test_project_and_unit_audience_match_resident(client, resident_unit, resident_headers, management_headers):
    project = await client.post(
        "/api/v1/management/announcements",
        json={
            "title": "Project notice",
            "content": "All residents in ONB can see this.",
            "scopes": [{"scope_type": "project", "project_code": "ONB"}],
        },
        headers=management_headers,
    )
    assert project.status_code == 201
    assert (
        await client.post(
            f"/api/v1/management/announcements/{project.json()['id']}/publish",
            json={"version": 0},
            headers=management_headers,
        )
    ).status_code == 200

    unit = await client.post(
        "/api/v1/management/announcements",
        json={
            "title": "Unit notice",
            "content": "Only this unit can see this.",
            "scopes": [{"scope_type": "unit", "unit_id": resident_unit["unit_id"]}],
        },
        headers=management_headers,
    )
    assert unit.status_code == 201
    assert (
        await client.post(
            f"/api/v1/management/announcements/{unit.json()['id']}/publish",
            json={"version": 0},
            headers=management_headers,
        )
    ).status_code == 200

    listed = await client.get("/api/v1/announcements", headers=resident_headers)
    assert listed.status_code == 200
    assert listed.json()["total"] == 2
