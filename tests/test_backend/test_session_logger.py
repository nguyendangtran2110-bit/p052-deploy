import json
from pathlib import Path
from uuid import uuid4

from src.backend.infrastructure.logging.session_logger import SessionLogger


def test_session_logger_writes_valid_jsonl(tmp_path: Path):
    logger = SessionLogger(log_dir=tmp_path, enabled=True)
    conv_id = str(uuid4())

    logger.log_turn(
        conversation_id=conv_id,
        actor_role="resident",
        actor_id="res-123",
        unit_id="unit-456",
        query="Giờ mở cửa bể bơi?",
        chat_history_length=2,
        retrieval={"chunks_count": 2, "top_score": 0.95},
        intent_detected="handbook_question",
        response_preview="Bể bơi mở cửa từ 06:00 đến 21:00.",
        citations_count=1,
        total_latency_ms=123.45,
    )

    log_files = list(tmp_path.glob("session_*.jsonl"))
    assert len(log_files) == 1

    lines = log_files[0].read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["conversation_id"] == conv_id
    assert entry["actor"]["role"] == "resident"
    assert entry["actor"]["id"] == "res-123"
    assert entry["actor"]["unit_id"] == "unit-456"
    assert entry["input"]["query"] == "Giờ mở cửa bể bơi?"
    assert entry["input"]["chat_history_length"] == 2
    assert entry["retrieval"]["chunks_count"] == 2
    assert entry["retrieval"]["top_score"] == 0.95
    assert entry["agent"]["intent"] == "handbook_question"
    assert entry["agent"]["citations_count"] == 1
    assert "Bể bơi mở cửa" in entry["output"]["response_preview"]
    assert entry["total_latency_ms"] == 123.45


def test_session_logger_disabled_writes_nothing(tmp_path: Path):
    logger = SessionLogger(log_dir=tmp_path, enabled=False)
    logger.log_turn(
        conversation_id=str(uuid4()),
        query="Hello",
    )

    log_files = list(tmp_path.glob("session_*.jsonl"))
    assert len(log_files) == 0


def test_session_logger_graceful_on_error(monkeypatch, tmp_path: Path):
    logger = SessionLogger(log_dir=tmp_path, enabled=True)

    def faulty_open(*args, **kwargs):
        raise OSError("Disk write error")

    monkeypatch.setattr(Path, "open", faulty_open)

    # Should not raise exception
    logger.log_turn(
        conversation_id=str(uuid4()),
        query="Test query",
    )
