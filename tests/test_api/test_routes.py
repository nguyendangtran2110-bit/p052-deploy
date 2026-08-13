import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_chat_empty_message(client):
    response = await client.post("/api/v1/chat", json={"message": ""})
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_agent_status(client):
    response = await client.get("/api/v1/status")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rag_chat_returns_retrieved_chunk_details(client, monkeypatch):
    class FakeRagAgent:
        async def ainvoke(self, state):
            return {
                "rag_response": {
                    "answer": "Hồ bơi mở cửa từ 06h00.",
                    "citations": [],
                    "confidence": 0.9,
                },
                "retrieved_chunks": [
                    {
                        "text": "Thời gian hoạt động hồ bơi: 06h00 đến 12h00.",
                        "source_file": "so-tay-phu-dong-sky-garden.pdf",
                        "page_number": 17,
                        "section_title": "Hồ bơi",
                        "score": 0.8765,
                    },
                    {
                        "text": "Hồ bơi không hoạt động vào thứ hai.",
                        "source_file": "so-tay-phu-dong-sky-garden.pdf",
                        "page_number": 18,
                        "section_title": "Bảo trì",
                        "score": 0.7654,
                    },
                ],
            }

    monkeypatch.setattr("src.api.routes.rag_agent", FakeRagAgent())

    response = await client.post("/api/v1/rag/chat", json={"message": "giờ mở cửa hồ bơi"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["chunks_used"] == 2
    assert payload["chunks"][0]["chunk_index"] == 1
    assert payload["chunks"][0]["page_number"] == 17
    assert payload["chunks"][0]["text"] == "Thời gian hoạt động hồ bơi: 06h00 đến 12h00."
    assert payload["chunks"][1]["chunk_index"] == 2
