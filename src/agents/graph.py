from __future__ import annotations

import re
from typing import Any

from langgraph.graph import END, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from src.agents.state import AgentState
from src.backend.core.config import get_settings


class AgentStructuredResult(BaseModel):
    """Small, serializable result boundary between the LLM and backend."""

    model_config = ConfigDict(extra="ignore")

    intent: str = "handbook_question"
    assistant_message: str = ""
    draft: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    action: dict[str, Any] | None = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    attachment_ids: list[str] = Field(default_factory=list)


class ProductionAgent:
    """LangGraph-compatible runtime with a safe local fallback.

    The backend remains the authority for validation and side effects. This
    runtime only extracts a draft and proposes an action.
    """

    async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
        settings = get_settings()
        if settings.openai_api_key.strip():
            try:
                result = await self._invoke_llm(state, settings)
                result["query"] = state.get("query") or state.get("message") or ""
                return result
            except Exception:
                # A temporary provider failure must not produce an invented
                # side effect. The deterministic path only proposes actions.
                pass
        result = self._fallback(state)
        result["query"] = state.get("query") or state.get("message") or ""
        return result

    async def _invoke_llm(self, state: dict[str, Any], settings) -> dict[str, Any]:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model=settings.model_name,
            api_key=settings.openai_api_key,
            temperature=settings.llm_temperature,
        ).with_structured_output(AgentStructuredResult)
        context = {
            "actor_role": state.get("actor_role"),
            "workflow_type": state.get("workflow_type"),
            "workflow_state": state.get("workflow_state"),
            "workflow_draft": state.get("workflow_draft") or {},
            "pending_action": state.get("pending_action"),
            "selected_unit_id": state.get("selected_unit_id") or state.get("metadata", {}).get("unit_id"),
            "messages": (state.get("messages") or state.get("metadata", {}).get("messages", []))[-12:],
            "handbook_results": state.get("handbook_results", []),
            "message": state.get("message") or state.get("query") or "",
        }
        system = (
            "You are the OnBxrd resident/management assistant. Return only the structured schema. "
            "Extract facts from the newest message and merge them with workflow_draft. "
            "Never invent UUIDs, audience identifiers, citations, or attachment IDs. "
            "For resident_ticket require category, priority, title, description, location and unit_id. "
            "For manager_announcement require title, content and scopes. "
            "Only propose create_ticket/create_announcement_draft/publish_announcement; never claim that "
            "a side effect happened. Use a stable pending action_id when it is present in context."
        )
        response = await llm.ainvoke(
            [
                SystemMessage(content=system),
                HumanMessage(content=str(context)),
            ]
        )
        parsed = response if isinstance(response, AgentStructuredResult) else AgentStructuredResult.model_validate(response)
        result = parsed.model_dump(mode="json")
        result["response"] = result["assistant_message"]
        return result

    def _fallback(self, state: dict[str, Any]) -> dict[str, Any]:
        message = str(state.get("message") or state.get("query") or "").strip()
        workflow_type = state.get("workflow_type")
        workflow_state = state.get("workflow_state")
        draft = dict(state.get("workflow_draft") or {})
        pending_action = state.get("pending_action") if isinstance(state.get("pending_action"), dict) else None
        if workflow_type == "manager_announcement" or state.get("actor_role") == "management":
            return self._manager_result(message, draft, workflow_state, pending_action)
        if workflow_type == "resident_ticket" or self._looks_like_ticket(message, draft):
            return self._ticket_result(state, message, draft, workflow_state, pending_action)
        handbook_results = state.get("handbook_results") or []
        if handbook_results:
            first = handbook_results[0]
            return {
                "response": first.get("content") or "Tôi chưa tìm thấy thông tin phù hợp trong handbook.",
                "assistant_message": first.get("content") or "Tôi chưa tìm thấy thông tin phù hợp trong handbook.",
                "intent": "handbook_question",
                "draft": {},
                "missing_fields": [],
                "action": None,
                "citations": [item.get("citation", {}) for item in handbook_results if item.get("citation")],
                "attachment_ids": [],
            }
        return {
            "response": "Tôi có thể trả lời câu hỏi trong handbook hoặc hỗ trợ tạo ticket.",
            "assistant_message": "Tôi có thể trả lời câu hỏi trong handbook hoặc hỗ trợ tạo ticket.",
            "intent": "handbook_question",
            "draft": {},
            "missing_fields": [],
            "action": None,
            "citations": [],
            "attachment_ids": [],
        }

    def _ticket_result(
        self,
        state: dict[str, Any],
        message: str,
        draft: dict[str, Any],
        workflow_state: str | None,
        pending_action: dict[str, Any] | None,
    ) -> dict[str, Any]:
        confirmation = self._is_confirmation(message)
        cancellation = self._is_cancellation(message)
        if cancellation and workflow_state not in {"completed", "cancelled", "published"}:
            return {
                "response": "Đã hủy yêu cầu tạo ticket.",
                "assistant_message": "Đã hủy yêu cầu tạo ticket.",
                "intent": "create_ticket",
                "draft": draft,
                "missing_fields": [],
                "action": {
                    "type": "cancelled",
                    "action_id": self._pending_id(pending_action),
                    "requires_confirmation": False,
                    "payload": {},
                },
                "citations": [],
                "attachment_ids": [],
            }

        metadata = state.get("metadata") if isinstance(state.get("metadata"), dict) else {}
        selected_unit_id = state.get("selected_unit_id") or metadata.get("unit_id")
        if selected_unit_id:
            draft.setdefault("unit_id", str(selected_unit_id))

        if message and not confirmation:
            self._merge_ticket_message(draft, message)
        if not draft.get("priority"):
            draft["priority"] = self._infer_priority(message)

        required = ["unit_id", "category", "priority", "title", "description", "location"]
        missing = [field for field in required if not str(draft.get(field) or "").strip()]
        if missing:
            field = missing[0]
            question = {
                "unit_id": "Vui lòng chọn căn hộ đang gặp sự cố.",
                "category": "Sự cố thuộc nhóm nào, ví dụ điện, nước hay tiện ích?",
                "priority": "Mức độ ưu tiên của sự cố là thấp, trung bình, cao hay khẩn cấp?",
                "title": "Bạn muốn đặt tiêu đề ngắn nào cho sự cố này?",
                "description": "Bạn có thể mô tả rõ hơn sự cố đang xảy ra không?",
                "location": "Sự cố xảy ra ở vị trí nào?",
            }[field]
            return {
                "response": question,
                "assistant_message": question,
                "intent": "create_ticket",
                "draft": draft,
                "missing_fields": missing,
                "action": {
                    "type": "ask_clarification",
                    "action_id": self._pending_id(pending_action),
                    "requires_confirmation": False,
                    "payload": {"field": field},
                },
                "citations": [],
                "attachment_ids": [],
            }

        action_id = self._pending_id(pending_action) if confirmation else None
        action = {
            "type": "create_ticket",
            "action_id": action_id,
            "requires_confirmation": True,
            "payload": draft,
        }
        if confirmation and pending_action and pending_action.get("type") == "create_ticket":
            action["action_id"] = str(pending_action.get("action_id"))
        response = "Thông tin đã đủ. Bạn có muốn tạo ticket này không?"
        if confirmation:
            response = "Đã tiếp nhận xác nhận. Đang tạo ticket của bạn."
        return {
            "response": response,
            "assistant_message": response,
            "intent": "create_ticket",
            "draft": draft,
            "missing_fields": [],
            "action": action,
            "citations": [],
            "attachment_ids": [],
        }

    def _manager_result(
        self,
        message: str,
        draft: dict[str, Any],
        workflow_state: str | None,
        pending_action: dict[str, Any] | None,
    ) -> dict[str, Any]:
        confirmation = self._is_confirmation(message)
        cancellation = self._is_cancellation(message)
        if cancellation and workflow_state not in {"published", "completed"}:
            return {
                "response": "Đã hủy quy trình tạo announcement.",
                "assistant_message": "Đã hủy quy trình tạo announcement.",
                "intent": "create_announcement",
                "draft": draft,
                "missing_fields": [],
                "action": {"type": "cancelled", "action_id": self._pending_id(pending_action), "requires_confirmation": False, "payload": {}},
                "citations": [],
                "attachment_ids": [],
            }

        if workflow_state == "awaiting_publish_confirmation" and (confirmation or self._mentions_publish(message)):
            action = {
                "type": "publish_announcement",
                "action_id": self._pending_id(pending_action),
                "requires_confirmation": True,
                "payload": pending_action.get("payload", {}) if pending_action else {},
            }
            response = "Bạn có muốn publish announcement này không?"
            if confirmation:
                response = "Đã tiếp nhận xác nhận publish announcement."
            return {
                "response": response,
                "assistant_message": response,
                "intent": "publish_announcement",
                "draft": draft,
                "missing_fields": [],
                "action": action,
                "citations": [],
                "attachment_ids": [],
            }

        if message and not confirmation:
            self._merge_announcement_message(draft, message)
        missing = []
        if not str(draft.get("title") or "").strip():
            missing.append("title")
        if not str(draft.get("content") or "").strip():
            missing.append("content")
        if not isinstance(draft.get("scopes"), list) or not draft["scopes"]:
            missing.append("scopes")
        if missing:
            question = {
                "title": "Announcement cần tiêu đề nào?",
                "content": "Nội dung announcement cần thông báo là gì?",
                "scopes": "Announcement áp dụng cho toàn bộ cư dân, dự án, tòa hay căn hộ nào?",
            }[missing[0]]
            return {
                "response": question,
                "assistant_message": question,
                "intent": "create_announcement",
                "draft": draft,
                "missing_fields": missing,
                "action": {"type": "ask_clarification", "action_id": self._pending_id(pending_action), "requires_confirmation": False, "payload": {"field": missing[0]}},
                "citations": [],
                "attachment_ids": [],
            }
        action = {
            "type": "create_announcement_draft",
            "action_id": self._pending_id(pending_action) if confirmation else None,
            "requires_confirmation": True,
            "payload": draft,
        }
        response = "Thông tin đã đủ. Bạn có muốn tạo announcement ở trạng thái draft không?"
        if confirmation:
            response = "Đã tiếp nhận xác nhận. Đang tạo announcement draft."
        return {
            "response": response,
            "assistant_message": response,
            "intent": "create_announcement",
            "draft": draft,
            "missing_fields": [],
            "action": action,
            "citations": [],
            "attachment_ids": [],
        }

    @staticmethod
    def _merge_ticket_message(draft: dict[str, Any], message: str) -> None:
        lower = message.lower()
        if not draft.get("category"):
            if any(word in lower for word in ("nước", "rò rỉ", "chảy", "leak", "ống")):
                draft["category"] = "plumbing"
            elif any(word in lower for word in ("điện", "đèn", "electric", "light")):
                draft["category"] = "electrical"
            elif any(word in lower for word in ("thang máy", "elevator", "hồ bơi", "gym")):
                draft["category"] = "facility"
            else:
                draft["category"] = "maintenance"
        if not draft.get("description"):
            draft["description"] = message
        elif not AgentRuntimeHelpers.is_short_location_reply(message):
            draft["description"] = f"{draft['description']}\n{message}"
        if not draft.get("title"):
            draft["title"] = message[:100].rstrip(".!?")
        if not draft.get("location"):
            location = AgentRuntimeHelpers.extract_location(message)
            if location:
                draft["location"] = location

    @staticmethod
    def _merge_announcement_message(draft: dict[str, Any], message: str) -> None:
        lower = message.lower()
        title_match = re.search(r"(?:tiêu đề|title)\s*[:：]\s*(.+)", message, re.IGNORECASE)
        if title_match:
            draft["title"] = title_match.group(1).strip()[:255]
        elif not draft.get("title"):
            draft["title"] = message[:120].rstrip(".!?")
        if not draft.get("content"):
            draft["content"] = message
        if "khẩn" in lower or "emergency" in lower:
            draft["priority"] = "urgent"
        elif "quan trọng" in lower or "important" in lower:
            draft["priority"] = "important"
        else:
            draft.setdefault("priority", "normal")
        if "bảo trì" in lower or "maintenance" in lower:
            draft["type"] = "maintenance"
        elif "sự kiện" in lower or "event" in lower:
            draft["type"] = "event"
        elif "khẩn cấp" in lower or "emergency" in lower:
            draft["type"] = "emergency"
        if not draft.get("scopes"):
            if any(text in lower for text in ("toàn bộ cư dân", "tất cả cư dân", "all residents")):
                draft["scopes"] = [{"scope_type": "all_residents"}]
            else:
                building_match = re.search(r"(?:tòa|toa|building)\s*([A-Za-z0-9]+)", message, re.IGNORECASE)
                if building_match:
                    draft["scopes"] = [{"scope_type": "building", "building": building_match.group(1).upper()}]
                else:
                    project_match = re.search(r"(?:dự án|project)\s*([A-Za-z0-9_-]+)", message, re.IGNORECASE)
                    if project_match:
                        draft["scopes"] = [{"scope_type": "project", "project_code": project_match.group(1).upper()}]

    @staticmethod
    def _looks_like_ticket(message: str, draft: dict[str, Any]) -> bool:
        if draft:
            return True
        lower = message.lower()
        return any(
            word in lower
            for word in (
                "tạo ticket",
                "create ticket",
                "sự cố",
                "bị hỏng",
                "không hoạt động",
                "rò rỉ",
                "chảy nước",
                "broken",
                "leak",
                "not working",
            )
        )

    @staticmethod
    def _infer_priority(message: str) -> str:
        lower = message.lower()
        if any(word in lower for word in ("khẩn", "nguy hiểm", "emergency", "urgent")):
            return "urgent"
        if any(word in lower for word in ("gấp", "ảnh hưởng", "high", "cao")):
            return "high"
        return "medium"

    @staticmethod
    def _is_confirmation(message: str) -> bool:
        normalized = re.sub(r"[^a-zA-ZÀ-ỹ0-9 ]", " ", message.lower()).strip()
        return normalized in {"được", "ok", "okay", "yes", "có", "xác nhận", "tạo đi", "publish", "đăng đi", "đồng ý"}

    @staticmethod
    def _is_cancellation(message: str) -> bool:
        normalized = message.lower().strip()
        return any(text in normalized for text in ("hủy", "huỷ", "cancel", "không tạo", "bỏ qua"))

    @staticmethod
    def _mentions_publish(message: str) -> bool:
        normalized = message.lower()
        return any(text in normalized for text in ("publish", "đăng", "phát hành", "xuất bản"))

    @staticmethod
    def _pending_id(action: dict[str, Any] | None) -> str | None:
        if not action or not action.get("action_id"):
            return None
        return str(action["action_id"])


class AgentRuntimeHelpers:
    @staticmethod
    def extract_location(message: str) -> str | None:
        match = re.search(r"(?:ở|tại|vị trí|khu vực|location)\s*[:：]?\s*([^,.!?]+)", message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        for phrase in ("phòng ngủ", "phòng khách", "bếp", "ban công", "hành lang", "thang máy"):
            if phrase in message.lower():
                return phrase
        floor_match = re.search(r"tầng\s*\d+", message, re.IGNORECASE)
        return floor_match.group(0) if floor_match else None

    @staticmethod
    def is_short_location_reply(message: str) -> bool:
        return len(message.split()) <= 8 and AgentRuntimeHelpers.extract_location(message) is not None


_runtime = ProductionAgent()


async def _assistant_node(state: AgentState) -> AgentState:
    result = await _runtime.ainvoke(dict(state))
    result.setdefault("response", result.get("assistant_message", ""))
    result.setdefault("workflow_id", state.get("workflow_id"))
    result.setdefault("workflow_type", state.get("workflow_type"))
    result.setdefault("state", state.get("workflow_state"))
    result.setdefault("workflow_version", state.get("workflow_version"))
    result.setdefault("error", None)
    return {**state, **result}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("assistant", _assistant_node)
    graph.set_entry_point("assistant")
    graph.add_edge("assistant", END)
    return graph.compile()


agent = build_graph()
