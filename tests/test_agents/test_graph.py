import pytest

from src.agents.graph import ProductionAgent, agent


@pytest.mark.asyncio
async def test_agent_basic_flow():
    result = await agent.ainvoke({"query": "Hello"})
    assert "response" in result


@pytest.mark.asyncio
async def test_agent_state_structure():
    result = await agent.ainvoke({"query": "Test query"})
    assert isinstance(result, dict)
    assert "query" in result


@pytest.mark.asyncio
async def test_agent_returns_typed_resident_ticket_preview():
    result = await agent.ainvoke(
        {
            "message": "Water leak in the kitchen at floor 12",
            "actor_role": "resident",
            "selected_unit_id": "00000000-0000-0000-0000-000000000001",
        }
    )

    assert result["workflow_type"] == "resident_ticket"
    assert result["intent"] == "create_ticket"
    assert result["draft"]["unit_id"] == "00000000-0000-0000-0000-000000000001"
    assert result["draft"]["category"] == "plumbing"
    assert result["draft"]["location"] == "floor 12"
    assert result["action"]["type"] == "create_ticket"
    assert result["action"]["action_id"]
    assert result["action"]["requires_confirmation"] is True
    assert result["state"] == "awaiting_confirmation"


@pytest.mark.asyncio
async def test_agent_uses_retrieved_handbook_context_without_side_effect():
    result = await agent.ainvoke(
        {
            "message": "What time does the pool close?",
            "actor_role": "resident",
            "handbook_results": [
                {
                    "content": "The pool closes at 21:00.",
                    "citation": {"title": "Handbook", "page": 18},
                }
            ],
        }
    )

    assert result["intent"] == "handbook_question"
    assert result["response"] == "The pool closes at 21:00."
    assert result["action"] is None
    assert result["citations"][0]["page"] == 18


@pytest.mark.asyncio
async def test_agent_answers_ticket_question_without_side_effect():
    result = await agent.ainvoke(
        {
            "message": "What is the ticket status?",
            "actor_role": "resident",
            "metadata": {"ticket": {"ticket_code": "TKT-001", "status": "submitted"}},
        }
    )

    assert result["intent"] == "ticket_question"
    assert "TKT-001" in result["response"]
    assert result["action"] is None


@pytest.mark.asyncio
async def test_agent_proposes_manager_draft_update_before_publish():
    result = await agent.ainvoke(
        {
            "message": "title: Elevator maintenance updated",
            "actor_role": "management",
            "workflow_type": "manager_announcement",
            "workflow_state": "awaiting_publish_confirmation",
            "workflow_draft": {
                "title": "Elevator maintenance",
                "content": "Elevator A will be serviced tomorrow.",
                "scopes": [{"scope_type": "all_residents"}],
            },
            "pending_action": {
                "type": "publish_announcement",
                "action_id": "00000000-0000-0000-0000-000000000010",
            },
        }
    )

    assert result["intent"] == "announcement_edit"
    assert result["action"]["type"] == "update_announcement"
    assert result["draft"]["title"] == "Elevator maintenance updated"


@pytest.mark.asyncio
async def test_manager_handbook_question_does_not_start_announcement_workflow():
    result = await agent.ainvoke(
        {
            "message": "What time does the pool close?",
            "actor_role": "management",
            "workflow_type": "manager_announcement",
            "workflow_state": "collecting",
            "handbook_results": [{"content": "The pool closes at 21:00."}],
        }
    )

    assert result["intent"] == "handbook_question"
    assert result["action"] is None
    assert result["draft"] == {}
    assert result["response"] == "The pool closes at 21:00."


@pytest.mark.asyncio
async def test_existing_ticket_message_does_not_create_another_ticket():
    result = await agent.ainvoke(
        {
            "message": "What is the ticket status?",
            "actor_role": "resident",
            "workflow_type": "resident_ticket",
            "workflow_state": "completed",
            "workflow_draft": {
                "unit_id": "00000000-0000-0000-0000-000000000001",
                "category": "plumbing",
                "priority": "medium",
                "title": "Water leak",
                "description": "Leak in the kitchen",
                "location": "kitchen",
            },
            "metadata": {"ticket": {"ticket_code": "TKT-001", "status": "submitted"}},
        }
    )

    assert result["intent"] == "ticket_question"
    assert result["action"] is None
    assert "TKT-001" in result["response"]


def test_agent_redacts_tokens_and_urls_before_prompt_state():
    prepared = ProductionAgent.prepare_state(
        {
            "message": "Bearer secret-token https://bucket.example/file?X-Amz-Signature=secret",
            "messages": [{"role": "user", "content": "refresh_token=secret"}],
        }
    )

    assert "secret-token" not in prepared["message"]
    assert "https://bucket.example" not in prepared["message"]
    assert "refresh_token=secret" not in prepared["messages"][0]["content"]
