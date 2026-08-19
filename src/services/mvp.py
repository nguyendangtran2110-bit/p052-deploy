"""Small, deterministic MVP service used by the demo API.

It deliberately keeps Zalo simulated and ticket creation human-confirmed.
"""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


KEYWORDS = {
    "plumbing": ("nước", "rò", "ống", "bồn rửa", "vòi"),
    "safety": ("cháy", "khói", "gas"),
    "electrical": ("điện", "mất điện", "chập điện"),
    "access": ("hỏng", "thang máy", "khóa", "cửa", "điều hòa", "máy lạnh", "mất mạng"),
}
RESOLVED_MARKERS = ("hết", "đã xong", "đã sửa", "không còn", "ổn rồi")
PROFILE = {"id": "resident-minh", "name": "Nguyễn Minh", "tower": "A", "floor": "12", "unit": "12B"}


class MvpService:
    def __init__(self, database_path: str = "data/onbxrd_demo.db") -> None:
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self.database_path = database_path
        self._initialize()

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connection() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS ticket_drafts (
                  id TEXT PRIMARY KEY, resident_id TEXT NOT NULL, title TEXT NOT NULL,
                  category TEXT NOT NULL, priority TEXT NOT NULL, location TEXT NOT NULL,
                  description TEXT NOT NULL, source_message TEXT NOT NULL, status TEXT NOT NULL,
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tickets (
                  id TEXT PRIMARY KEY, draft_id TEXT NOT NULL, resident_id TEXT NOT NULL,
                  title TEXT NOT NULL, category TEXT NOT NULL, priority TEXT NOT NULL,
                  location TEXT NOT NULL, description TEXT NOT NULL, source_channel TEXT NOT NULL,
                  status TEXT NOT NULL, assigned_manager TEXT, created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS ticket_events (
                  id TEXT PRIMARY KEY, ticket_id TEXT NOT NULL, actor_role TEXT NOT NULL,
                  event_type TEXT NOT NULL, note TEXT, created_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def detect(self, message: str) -> dict | None:
        normalized = message.casefold().strip()
        if not normalized or any(marker in normalized for marker in RESOLVED_MARKERS):
            return None
        for category, words in KEYWORDS.items():
            if any(word in normalized for word in words):
                return {"category": category, "priority": "High" if category in {"safety", "electrical", "plumbing"} else "Medium"}
        return None

    def create_draft(self, message: str) -> dict:
        detection = self.detect(message)
        if detection is None:
            raise ValueError("Message is not an actionable issue")
        draft = self.preview_draft(message, detection)
        with self._connection() as db:
            db.execute(
                "INSERT INTO ticket_drafts VALUES (:id, :resident_id, :title, :category, :priority, :location, :description, :source_message, :status, :created_at)",
                draft,
            )
        return draft

    def preview_draft(self, message: str, detection: dict | None = None) -> dict:
        detection = detection or self.detect(message)
        if detection is None:
            raise ValueError("Message is not an actionable issue")
        category = detection["category"]
        title = {
            "plumbing": "Water issue reported in kitchen",
            "safety": "Safety issue reported",
            "electrical": "Electrical issue reported",
            "access": "Building access or equipment issue reported",
        }[category]
        draft = {
            "id": str(uuid4()), "resident_id": PROFILE["id"], "title": title,
            "category": category.title(), "priority": detection["priority"],
            "location": f"Tower {PROFILE['tower']} · Floor {PROFILE['floor']} · Unit {PROFILE['unit']} · Kitchen",
            "description": message, "source_message": message, "status": "DRAFT", "created_at": self._now(),
        }
        return draft

    def get_draft(self, draft_id: str) -> dict | None:
        with self._connection() as db:
            row = db.execute("SELECT * FROM ticket_drafts WHERE id = ?", (draft_id,)).fetchone()
        return dict(row) if row else None

    def submit_draft(self, draft_id: str, actor_role: str) -> dict:
        if actor_role != "resident":
            raise PermissionError("Only the resident can submit a ticket draft")
        draft = self.get_draft(draft_id)
        if draft is None:
            raise LookupError("Ticket draft not found")
        if draft["status"] != "DRAFT":
            raise ValueError("Ticket draft has already been submitted")
        now = self._now()
        ticket = {**draft, "id": str(uuid4()), "draft_id": draft_id, "source_channel": "app", "status": "SUBMITTED", "assigned_manager": None, "updated_at": now}
        with self._connection() as db:
            db.execute("UPDATE ticket_drafts SET status = 'SUBMITTED' WHERE id = ?", (draft_id,))
            db.execute(
                "INSERT INTO tickets (id,draft_id,resident_id,title,category,priority,location,description,source_channel,status,assigned_manager,created_at,updated_at) VALUES (:id,:draft_id,:resident_id,:title,:category,:priority,:location,:description,:source_channel,:status,:assigned_manager,:created_at,:updated_at)", ticket,
            )
            self._event(db, ticket["id"], "resident", "SUBMITTED", "Resident explicitly submitted the reviewed draft")
        return ticket

    def update_ticket(self, ticket_id: str, actor_role: str, status: str, note: str | None = None, assigned_manager: str | None = None) -> dict:
        if actor_role != "manager":
            raise PermissionError("Only a manager can update tickets")
        with self._connection() as db:
            row = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
            if not row:
                raise LookupError("Ticket not found")
            ticket = dict(row)
            transitions = {"SUBMITTED": {"APPROVED", "REJECTED"}, "APPROVED": {"IN_PROGRESS"}, "IN_PROGRESS": {"RESOLVED"}}
            if status not in transitions.get(ticket["status"], set()):
                raise ValueError("Invalid ticket status transition")
            if status in {"REJECTED", "RESOLVED"} and not (note or "").strip():
                raise ValueError("A note is required for this status")
            now = self._now()
            db.execute("UPDATE tickets SET status = ?, assigned_manager = COALESCE(?, assigned_manager), updated_at = ? WHERE id = ?", (status, assigned_manager, now, ticket_id))
            self._event(db, ticket_id, actor_role, status, note)
            updated = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        return dict(updated)

    def tickets(self) -> list[dict]:
        with self._connection() as db:
            return [dict(row) for row in db.execute("SELECT * FROM tickets ORDER BY updated_at DESC")]

    def contact_resident(self, ticket_id: str, actor_role: str) -> dict:
        if actor_role != "manager":
            raise PermissionError("Only a manager can contact a resident")
        with self._connection() as db:
            if not db.execute("SELECT 1 FROM tickets WHERE id = ?", (ticket_id,)).fetchone():
                raise LookupError("Ticket not found")
            self._event(db, ticket_id, actor_role, "CONTACT_ATTEMPT", "Demo mode: Zalo unavailable; in-app notification fallback sent")
        return {"channel": "in_app", "status": "fallback_sent", "message": "Contact attempt recorded. In-app notification sent; Zalo OA is simulated in this demo."}

    @staticmethod
    def _event(db: sqlite3.Connection, ticket_id: str, actor_role: str, event_type: str, note: str | None) -> None:
        db.execute("INSERT INTO ticket_events VALUES (?, ?, ?, ?, ?, ?)", (str(uuid4()), ticket_id, actor_role, event_type, note, datetime.now(UTC).isoformat()))


mvp_service = MvpService()
