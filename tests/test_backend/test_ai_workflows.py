import pytest

from src.backend.api.dependencies import get_agent_runtime
from src.main import app


class ResidentWorkflowAgent:
    def __init__(self, unit_id: str):
        self.unit_id = unit_id
        self.calls = 0

    async def ainvoke(self, state):
        self.calls += 1
        if self.calls == 1:
            return {
                "response": "Sự cố xảy ra ở vị trí nào?",
                "intent": "create_ticket",
                "draft": {
                    "unit_id": self.unit_id,
                    "category": "plumbing",
                    "priority": "high",
                    "title": "Rò rỉ nước",
                    "description": "Nước chảy dưới bồn rửa.",
                },
                "missing_fields": ["location"],
                "action": {
                    "type": "ask_clarification",
                    "action_id": "00000000-0000-0000-0000-000000000001",
                    "requires_confirmation": False,
                    "payload": {"field": "location"},
                },
            }
        return {
            "response": "Thông tin đã đủ. Bạn có muốn tạo ticket không?",
            "intent": "create_ticket",
            "draft": {"location": "Bếp"},
            "action": {
                "type": "create_ticket",
                "action_id": "00000000-0000-0000-0000-000000000002",
                "requires_confirmation": True,
            },
        }


class ManagerWorkflowAgent:
    def __init__(self):
        self.calls = 0

    async def ainvoke(self, _state):
        self.calls += 1
        if self.calls == 1:
            return {
                "response": "Đã đủ thông tin. Xác nhận tạo draft announcement?",
                "intent": "create_announcement",
                "draft": {
                    "title": "Bảo trì thang máy",
                    "content": "Thang máy tòa A sẽ được bảo trì ngày mai.",
                    "type": "maintenance",
                    "priority": "important",
                    "scopes": [{"scope_type": "building", "project_code": "ONB", "building": "A"}],
                },
                "action": {
                    "type": "create_announcement_draft",
                    "action_id": "00000000-0000-0000-0000-000000000011",
                    "requires_confirmation": True,
                },
            }
        if self.calls == 2:
            return {
                "response": "Đã tạo draft. Xác nhận publish?",
                "intent": "create_announcement",
                "action": {
                    "type": "create_announcement_draft",
                    "action_id": "00000000-0000-0000-0000-000000000011",
                    "requires_confirmation": True,
                },
            }
        return {
            "response": "Đang publish announcement.",
            "intent": "publish_announcement",
            "action": {
                "type": "publish_announcement",
                "action_id": "00000000-0000-0000-0000-000000000012",
                "requires_confirmation": True,
            },
        }


class ManagerHandbookAgent:
    async def ainvoke(self, _state):
        return {
            "response": "The pool closes at 21:00.",
            "intent": "handbook_question",
            "draft": {},
            "missing_fields": [],
            "action": None,
            "citations": [{"title": "Handbook", "page": 18}],
        }


@pytest.mark.asyncio
async def test_resident_workflow_collects_then_confirms_once(client, resident_unit, resident_headers):
    agent = ResidentWorkflowAgent(resident_unit["unit_id"])
    app.dependency_overrides[get_agent_runtime] = lambda: agent
    try:
        first = await client.post(
            "/api/v1/chat/messages",
            headers=resident_headers,
            json={"message": "Máy nước bị rò rỉ", "unit_id": resident_unit["unit_id"]},
        )
        assert first.status_code == 200, first.text
        assert first.json()["state"] == "collecting"
        assert first.json()["missing_fields"] == ["location"]
        workflow_id = first.json()["workflow_id"]
        workflow_version = first.json()["workflow_version"]

        preview = await client.post(
            "/api/v1/chat/messages",
            headers=resident_headers,
            json={
                "message": "Ở bếp",
                "conversation_id": first.json()["conversation_id"],
                "workflow_id": workflow_id,
                "workflow_version": workflow_version,
            },
        )
        assert preview.status_code == 200, preview.text
        assert preview.json()["state"] == "awaiting_confirmation"
        action_id = preview.json()["action"]["action_id"]

        confirmed = await client.post(
            "/api/v1/chat/messages",
            headers=resident_headers,
            json={
                "message": "Xác nhận",
                "conversation_id": preview.json()["conversation_id"],
                "workflow_id": workflow_id,
                "workflow_version": preview.json()["workflow_version"],
                "confirmed_action_id": action_id,
                "confirm_action": True,
            },
        )
        assert confirmed.status_code == 200, confirmed.text
        assert confirmed.json()["state"] == "completed"
        assert confirmed.json()["ticket"]["source"] == "chat"
        assert confirmed.json()["ticket"]["location"] == "Bếp"
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)


@pytest.mark.asyncio
async def test_manager_handbook_question_does_not_create_announcement_action(client, management_headers):
    app.dependency_overrides[get_agent_runtime] = ManagerHandbookAgent
    try:
        created = await client.post("/api/v1/management/assistant/conversations", headers=management_headers)
        assert created.status_code == 201, created.text
        conversation_id = created.json()["conversation_id"]
        workflow_id = created.json()["workflow_id"]

        response = await client.post(
            f"/api/v1/management/assistant/conversations/{conversation_id}/messages",
            headers=management_headers,
            json={
                "message": "What time does the pool close?",
                "workflow_id": workflow_id,
                "workflow_version": 0,
            },
        )

        assert response.status_code == 200, response.text
        assert response.json()["state"] == "collecting"
        assert response.json()["missing_fields"] == []
        assert response.json()["action"] is None
        assert response.json()["announcement"] is None
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)


@pytest.mark.asyncio
async def test_manager_workflow_creates_draft_before_publish_confirmation(
    client, management_headers
):
    agent = ManagerWorkflowAgent()
    app.dependency_overrides[get_agent_runtime] = lambda: agent
    try:
        created = await client.post("/api/v1/management/assistant/conversations", headers=management_headers)
        assert created.status_code == 201, created.text
        conversation_id = created.json()["conversation_id"]
        workflow_id = created.json()["workflow_id"]

        preview = await client.post(
            f"/api/v1/management/assistant/conversations/{conversation_id}/messages",
            headers=management_headers,
            json={
                "message": "Soạn thông báo bảo trì thang máy tòa A",
                "workflow_id": workflow_id,
                "workflow_version": 0,
            },
        )
        assert preview.status_code == 200, preview.text
        assert preview.json()["state"] == "awaiting_confirmation"

        draft = await client.post(
            f"/api/v1/management/assistant/conversations/{conversation_id}/messages",
            headers=management_headers,
            json={
                "message": "Xác nhận tạo draft",
                "workflow_id": workflow_id,
                "workflow_version": preview.json()["workflow_version"],
                "confirmed_action_id": preview.json()["action"]["action_id"],
                "confirm_action": True,
            },
        )
        assert draft.status_code == 200, draft.text
        assert draft.json()["state"] == "awaiting_publish_confirmation"
        assert draft.json()["announcement"]["status"] == "draft"
        publish_action = draft.json()["action"]["next_action"]

        published = await client.post(
            f"/api/v1/management/assistant/conversations/{conversation_id}/messages",
            headers=management_headers,
            json={
                "message": "Xác nhận publish",
                "workflow_id": workflow_id,
                "workflow_version": draft.json()["workflow_version"],
                "confirmed_action_id": publish_action["action_id"],
                "confirm_action": True,
            },
        )
        assert published.status_code == 200, published.text
        assert published.json()["state"] == "published"
        assert published.json()["announcement"]["status"] == "published"
    finally:
        app.dependency_overrides.pop(get_agent_runtime, None)
