from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from src.backend.core.config import get_settings

logger = logging.getLogger(__name__)


def _json_serial(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return str(obj)


class SessionLogger:
    """Thread-safe, append-only structured session logger for AI chatbot telemetry.

    Logs execution events (queries, retrieval scores, LLM latencies, routing decisions)
    to daily JSONL files in `data/logs/chat_sessions/`.
    """

    def __init__(self, log_dir: Path | str | None = None, enabled: bool | None = None):
        settings = get_settings()
        self.enabled = enabled if enabled is not None else settings.chat_log_enabled
        configured_dir = log_dir if log_dir is not None else settings.chat_log_dir
        self.log_dir = Path(configured_dir)

    def _get_daily_log_file(self) -> Path:
        today_str = datetime.now(UTC).strftime("%Y-%m-%d")
        return self.log_dir / f"session_{today_str}.jsonl"

    def log_turn(
        self,
        *,
        conversation_id: str | UUID,
        turn_id: str | None = None,
        actor_role: str = "resident",
        actor_id: str | None = None,
        unit_id: str | None = None,
        query: str = "",
        chat_history_length: int = 0,
        retrieval: dict[str, Any] | None = None,
        intent_detected: str | None = None,
        workflow_type: str | None = None,
        workflow_state: str | None = None,
        action: dict[str, Any] | None = None,
        ticket: dict[str, Any] | None = None,
        response_preview: str = "",
        citations_count: int = 0,
        llm: dict[str, Any] | None = None,
        total_latency_ms: float | None = None,
        error: str | None = None,
    ) -> None:
        """Record a single chat turn telemetry event."""
        if not self.enabled:
            return

        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            log_file = self._get_daily_log_file()

            event = {
                "timestamp": datetime.now(UTC).isoformat(),
                "conversation_id": str(conversation_id),
                "turn_id": turn_id or f"turn-{int(datetime.now(UTC).timestamp() * 1000)}",
                "actor": {
                    "role": actor_role,
                    "id": str(actor_id) if actor_id else None,
                    "unit_id": str(unit_id) if unit_id else None,
                },
                "input": {
                    "query": query,
                    "chat_history_length": chat_history_length,
                },
                "retrieval": retrieval or {},
                "agent": {
                    "intent": intent_detected,
                    "workflow_type": workflow_type,
                    "workflow_state": workflow_state,
                    "action": action,
                    "ticket": ticket,
                    "citations_count": citations_count,
                },
                "output": {
                    "response_preview": response_preview[:300] if response_preview else "",
                },
                "llm": llm or {},
                "total_latency_ms": round(total_latency_ms, 2) if total_latency_ms is not None else None,
                "error": error,
            }

            serialized = json.dumps(event, default=_json_serial, ensure_ascii=False)
            with log_file.open("a", encoding="utf-8") as f:
                f.write(serialized + "\n")
        except Exception as exc:
            # Observability logging should never crash user-facing requests
            logger.warning("Failed to write session log: %s", exc)
