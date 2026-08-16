from types import SimpleNamespace

import pytest

import src.agents.graph as graph_module
from src.agents.graph import ProductionAgent


@pytest.mark.asyncio
async def test_llm_classifies_manager_announcement_intent(monkeypatch):
    monkeypatch.setattr(graph_module, "get_settings", lambda: SimpleNamespace(openai_api_key="test-key"))

    async def llm_result(_state, _settings, *, strict=False):
        return {
            "assistant_message": "Kiem tra draft announcement va xac nhan tao draft.",
            "intent": "create_announcement",
            "draft": {
                "title": "Lich bao tri dinh ky",
                "content": "Ngay mai co lich bao tri dinh ky.",
                "type": "maintenance",
                "priority": "normal",
                "scopes": [{"scope_type": "all_residents"}],
            },
            "missing_fields": [],
            "action": {"type": "create_announcement_draft", "requires_confirmation": True},
            "citations": [],
        }

    agent = ProductionAgent()
    monkeypatch.setattr(agent, "_invoke_llm", llm_result)
    monkeypatch.setattr(agent, "_fallback", lambda _state: pytest.fail("fallback must not run on the LLM path"))

    result = await agent.ainvoke(
        {
            "message": "Thong bao cho dan cu ngay mai co lich bao tri dinh ky",
            "actor_role": "management",
            "workflow_type": "manager_announcement",
            "workflow_state": "collecting",
            "workflow_draft": {},
            "pending_action": None,
            "handbook_results": [],
        }
    )

    assert result["intent"] == "create_announcement"
    assert result["draft"]["type"] == "maintenance"
    assert result["draft"]["scopes"] == [{"scope_type": "all_residents"}]
    assert result["action"]["type"] == "create_announcement_draft"


@pytest.mark.asyncio
async def test_llm_infers_all_residents_scope_from_manager_phrase(monkeypatch):
    monkeypatch.setattr(graph_module, "get_settings", lambda: SimpleNamespace(openai_api_key="test-key"))

    async def llm_result(_state, _settings, *, strict=False):
        return {
            "assistant_message": "Xác nhận tạo thông báo cho cư dân?",
            "intent": "create_announcement",
            "draft": {
                "title": "Lịch bảo trì định kỳ",
                "content": "Ngày mai có lịch bảo trì định kỳ.",
                "type": "general",
                "priority": "normal",
                "scopes": [],
            },
            "missing_fields": ["scopes"],
            "action": {"type": "create_announcement_draft", "requires_confirmation": True},
            "citations": [],
        }

    agent = ProductionAgent()
    monkeypatch.setattr(agent, "_invoke_llm", llm_result)

    result = await agent.ainvoke(
        {
            "message": "Tạo announcement thông báo lịch bảo trì định kỳ đến cư dân vào ngày mai",
            "actor_role": "management",
            "workflow_type": "manager_announcement",
            "workflow_state": "collecting",
            "workflow_draft": {},
            "pending_action": None,
            "handbook_results": [],
        }
    )

    assert result["draft"]["scopes"] == [{"scope_type": "all_residents"}]
    assert result["missing_fields"] == []
