import json
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

    monkeypatch.setattr("src.backend.api.routes.rag.rag_agent", FakeRagAgent())

    response = await client.post("/api/v1/rag/chat", json={"message": "giờ mở cửa hồ bơi"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["chunks_used"] == 2
    assert payload["chunks"][0]["chunk_index"] == 1
    assert payload["chunks"][0]["page_number"] == 17
    assert payload["chunks"][0]["text"] == "Thời gian hoạt động hồ bơi: 06h00 đến 12h00."
    assert payload["chunks"][1]["chunk_index"] == 2


@pytest.mark.asyncio
async def test_chat_messages_streams_rag_answer(client, monkeypatch):
    class Chunk:
        def to_dict(self):
            return {
                "text": "Các tiện ích gồm hồ bơi và phòng gym.",
                "source_file": "phu-dong.md",
                "page_number": 5,
                "section_title": "Tiện ích",
                "score": 0.9,
            }

    monkeypatch.setattr("src.backend.api.routes.chat.retrieve_context", lambda *_args, **_kwargs: [Chunk()])
    monkeypatch.setattr(
        "src.backend.api.routes.chat.stream_rag_answer",
        lambda *_args, **_kwargs: iter(["Các tiện ích ", "gồm hồ bơi và phòng gym."]),
    )

    response = await client.post(
        "/api/v1/chat/messages",
        json={"message": "liệt kê các tiện ích"},
        headers={"Accept": "text/event-stream"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"type": "token"' in response.text
    assert '"type": "done"' in response.text
    assert "Các tiện ích gồm hồ bơi và phòng gym." in response.text


@pytest.mark.asyncio
async def test_chat_messages_streams_rag_answer_with_history(client, monkeypatch):
    class Chunk:
        def to_dict(self):
            return {
                "text": "Hồ bơi mở cửa từ 06:00.",
                "source_file": "phu-dong.md",
                "page_number": 5,
                "section_title": "Hồ bơi",
                "score": 0.95,
            }

    history_passed = []

    def mock_stream_rag_answer(query, chunks, chat_history=None):
        if chat_history:
            history_passed.extend(chat_history)
        yield "Hồ bơi mở cửa lúc 06:00."

    monkeypatch.setattr("src.backend.api.routes.chat.retrieve_context", lambda *_args, **_kwargs: [Chunk()])
    monkeypatch.setattr("src.backend.api.routes.chat.stream_rag_answer", mock_stream_rag_answer)

    # First turn
    turn1 = await client.post(
        "/api/v1/chat/messages",
        json={"message": "Hồ bơi ở đâu?"},
        headers={"Accept": "text/event-stream"},
    )
    assert turn1.status_code == 200
    lines = [json.loads(line[6:]) for line in turn1.text.split("\n\n") if line.startswith("data: ")]
    done_event = next(e for e in lines if e.get("type") == "done")
    conv_id = done_event["conversation_id"]

    # Second turn with conversation_id
    turn2 = await client.post(
        "/api/v1/chat/messages",
        json={"message": "Mấy giờ mở cửa?", "conversation_id": conv_id},
        headers={"Accept": "text/event-stream"},
    )
    assert turn2.status_code == 200
    assert len(history_passed) >= 1
    assert any("Hồ bơi ở đâu?" in str(h.get("content", "")) for h in history_passed)

