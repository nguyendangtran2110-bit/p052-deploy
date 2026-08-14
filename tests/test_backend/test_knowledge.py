import pytest


@pytest.mark.asyncio
async def test_management_can_upload_and_list_handbook(client, management_headers):
    uploaded = await client.post(
        "/api/v1/knowledge/documents",
        headers=management_headers,
        data={
            "title": "Resident Handbook 2026",
            "document_type": "handbook",
            "version": "2026.1",
            "project_code": "ONB",
            "building": "A",
        },
        files={"file": ("handbook.md", b"# Pool rules\nOpen 06:00-21:00", "text/markdown")},
    )
    listed = await client.get("/api/v1/knowledge/documents", headers=management_headers)

    assert uploaded.status_code == 201
    assert uploaded.json()["status"] == "pending"
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["title"] == "Resident Handbook 2026"


@pytest.mark.asyncio
async def test_resident_cannot_upload_handbook(client, resident_headers):
    response = await client.post(
        "/api/v1/knowledge/documents",
        headers=resident_headers,
        data={"title": "Unauthorized handbook"},
        files={"file": ("handbook.md", b"content", "text/markdown")},
    )

    assert response.status_code == 403
