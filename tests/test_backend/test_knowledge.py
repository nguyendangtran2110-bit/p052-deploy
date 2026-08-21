from pathlib import Path

import pytest

from src.backend.application.knowledge.search import KnowledgeSearchService


def test_local_handbook_search_ranks_relevant_chunk():
    handbook = Path(".test-handbook-search.md")
    handbook.write_text(
        "# Handbook\n\n"
        "**2.12. Vat nuoi**\n\n"
        "Cac loai vat nuoi khong duoc phep nuoi bao gom dong vat co doc va Pitbull.\n\n"
        "**2.13. Khach**\n\n"
        "Khach phai dang ky voi Ban Quan Ly khi ra vao.\n",
        encoding="utf-8",
    )
    try:
        service = KnowledgeSearchService(None)
        service.context_file = handbook

        results = service._search_local("Are pets such as Pitbull allowed?", limit=3)

        assert results
        assert "Pitbull" in results[0]["content"]
        assert results[0]["citation"]["source_type"] == "local_file"
        assert results[0]["citation"]["line_start"] <= results[0]["citation"]["line_end"]
    finally:
        handbook.unlink(missing_ok=True)

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
