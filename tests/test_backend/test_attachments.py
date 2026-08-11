from unittest.mock import AsyncMock

import pytest

from src.backend.api.dependencies import get_settings
from src.backend.core.config import Settings
from src.backend.infrastructure.storage import S3Storage
from src.main import app


@pytest.mark.asyncio
async def test_presigned_attachment_can_be_attached_to_ticket(client, resident_unit, resident_headers, monkeypatch):
    settings = Settings(aws_s3_bucket_name="test-private-bucket", aws_region="ap-southeast-1")
    app.dependency_overrides[get_settings] = lambda: settings
    upload = AsyncMock(return_value="https://s3.test/upload")
    download = AsyncMock(return_value="https://s3.test/download")
    monkeypatch.setattr(S3Storage, "create_presigned_upload", upload)
    monkeypatch.setattr(S3Storage, "create_presigned_download", download)
    try:
        presigned = await client.post(
            "/api/v1/attachments/presign",
            headers=resident_headers,
            json={
                "filename": "water-leak.png",
                "content_type": "image/png",
                "size_bytes": 2048,
            },
        )
        assert presigned.status_code == 201, presigned.text
        attachment_id = presigned.json()["id"]

        created = await client.post(
            "/api/v1/tickets",
            headers=resident_headers,
            json={
                "unit_id": resident_unit["unit_id"],
                "category": "maintenance",
                "priority": "medium",
                "title": "Water leak",
                "description": "There is water leaking in the kitchen.",
                "location": "Kitchen",
                "attachment_ids": [attachment_id],
            },
        )
        assert created.status_code == 201, created.text
        assert created.json()["attachments"][0]["id"] == attachment_id

        downloaded = await client.get(
            f"/api/v1/attachments/{attachment_id}/download",
            headers=resident_headers,
        )
        assert downloaded.status_code == 200
        assert downloaded.json()["download_url"] == "https://s3.test/download"
        upload.assert_awaited_once()
        download.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_settings, None)
