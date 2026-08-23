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
async def test_search_uses_vector_search_when_available(monkeypatch):
    from src.services.rag import RetrievedChunk

    mock_chunk = RetrievedChunk(
        text="Gym mở cửa từ 05:30 đến 22:00 mỗi ngày.",
        source_file="so-tay-phu-dong-sky-garden.pdf",
        page_number=18,
        section_title="Sử dụng tiện ích - Phòng Gym",
        score=0.92,
    )

    def mock_retrieve_context(query: str, top_k: int = 5, building_id: str | None = None):
        return [mock_chunk]

    monkeypatch.setattr("src.services.rag.retrieve_context", mock_retrieve_context)

    service = KnowledgeSearchService(None)
    results = await service.search("Giờ mở cửa phòng gym là mấy giờ?")

    assert len(results) == 1
    assert "Gym mở cửa" in results[0]["content"]
    assert results[0]["citation"]["source_type"] == "vector_store"
    assert results[0]["citation"]["title"] == "so-tay-phu-dong-sky-garden.pdf"
    assert results[0]["citation"]["page"] == 18
    assert results[0]["citation"]["section"] == "Sử dụng tiện ích - Phòng Gym"
    assert results[0]["citation"]["score"] == 0.92


@pytest.mark.asyncio
async def test_search_falls_back_to_local_when_vector_empty(monkeypatch):
    def mock_retrieve_context(query: str, top_k: int = 5, building_id: str | None = None):
        return []

    monkeypatch.setattr("src.services.rag.retrieve_context", mock_retrieve_context)

    handbook = Path(".test-handbook-fallback.md")
    handbook.write_text(
        "# Quy dinh be boi\n\nBe boi mo cua tu 06:00 den 21:00.\n",
        encoding="utf-8",
    )
    try:
        service = KnowledgeSearchService(None)
        service.context_file = handbook

        results = await service.search("be boi mo cua may gio?")
        assert len(results) == 1
        assert "Be boi" in results[0]["content"]
        assert results[0]["citation"]["source_type"] == "local_file"
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
