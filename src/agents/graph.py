from __future__ import annotations

import re
import unicodedata
from typing import Any
from uuid import uuid4

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError as PydanticValidationError

from src.agents.contracts import (
    AgentInput,
    AgentResult,
    AgentStructuredResult,
    AnnouncementDraft,
    TicketDraft,
)
from src.agents.prompts import AGENT_SYSTEM_PROMPT
from src.agents.state import AgentState
from src.backend.core.config import get_settings
from src.backend.security.chat_guardrails import sanitize_user_text


import logging

logger = logging.getLogger(__name__)


class ProductionAgent:
    """LangGraph-compatible runtime with a safe local fallback.

    The backend remains the authority for validation and side effects. This
    runtime only extracts a draft and proposes an action.
    """

    def _resolve_llm_config(self, settings) -> tuple[str, str | None, str] | None:
        """Resolve (api_key, base_url, model_name) using OpenAI, Qwen, or Groq."""
        if getattr(settings, "app_env", "") == "test":
            return None

        openai_key = settings.openai_api_key.strip()
        if openai_key and not openai_key.startswith(("sk-your-key", "your-openai")):
            return openai_key, settings.openai_api_base or None, settings.model_name

        qwen_key = settings.qwen_api_key.strip()
        if qwen_key and not qwen_key.startswith(("your-qwen", "sk-your-key")):
            base_url = settings.qwen_api_base or "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
            model = settings.qwen_model_name or settings.model_name or "qwen-plus"
            return qwen_key, base_url, model

        groq_key = settings.groq_api_key.strip()
        if groq_key and not groq_key.startswith(("gsk_your", "your-groq")):
            base_url = settings.groq_api_base or "https://api.groq.com/openai/v1"
            model = settings.groq_model_name or "llama-3.3-70b-versatile"
            return groq_key, base_url, model

        return None

    async def ainvoke(self, state: AgentInput) -> AgentResult:
        safe_state = self.prepare_state(state)
        settings = get_settings()
        llm_config = self._resolve_llm_config(settings)
        if llm_config is not None:
            api_key, base_url, model_name = llm_config
            try:
                result = await self._invoke_llm(safe_state, settings, api_key=api_key, base_url=base_url, model_name=model_name)
                return self._complete_result(result, safe_state)
            except Exception as exc:
                logger.warning("Primary LLM invocation failed (%s: %s), trying strict mode...", type(exc).__name__, exc)
                try:
                    result = await self._invoke_llm(
                        safe_state, settings, api_key=api_key, base_url=base_url, model_name=model_name, strict=True
                    )
                    return self._complete_result(result, safe_state)
                except Exception as strict_exc:
                    logger.warning("Strict LLM invocation failed (%s: %s), falling back to offline handler.", type(strict_exc).__name__, strict_exc)
        return self._complete_result(self._fallback(safe_state), safe_state)

    @staticmethod
    def prepare_state(state: dict[str, Any]) -> dict[str, Any]:
        """Normalize and redact the input before it reaches a prompt/node."""
        normalized = dict(state)
        normalized["message"] = ProductionAgent._redact_text(
            str(state.get("message") or state.get("query") or "").strip()
        )
        normalized["query"] = normalized["message"]
        normalized["workflow_draft"] = ProductionAgent._redact_value(dict(state.get("workflow_draft") or {}))
        normalized["pending_action"] = (
            ProductionAgent._redact_value(dict(state["pending_action"]))
            if isinstance(state.get("pending_action"), dict)
            else None
        )
        normalized["messages"] = ProductionAgent._safe_messages(state.get("messages") or [])
        normalized["metadata"] = ProductionAgent._redact_value(state.get("metadata") or {})
        normalized["handbook_results"] = ProductionAgent._safe_handbook_results(state.get("handbook_results"))
        return normalized

    async def _invoke_llm(
        self,
        state: dict[str, Any],
        settings,
        *,
        api_key: str,
        base_url: str | None,
        model_name: str,
        strict: bool = False,
    ) -> dict[str, Any]:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        extra_body: dict[str, Any] = {}
        if base_url and "aliyuncs.com" in base_url:
            extra_body["enable_thinking"] = False

        llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=settings.llm_temperature,
            extra_body=extra_body if extra_body else None,
        ).with_structured_output(
            AgentStructuredResult,
            method="function_calling",
        )
        context = {
            "actor_role": state.get("actor_role"),
            "workflow_type": state.get("workflow_type"),
            "workflow_state": state.get("workflow_state"),
            "workflow_draft": state.get("workflow_draft") or {},
            "pending_action": state.get("pending_action"),
            "selected_unit_id": state.get("selected_unit_id") or state.get("metadata", {}).get("unit_id"),
            "messages": (state.get("messages") or state.get("metadata", {}).get("messages", []))[-12:],
            "handbook_results": state.get("handbook_results", []),
            "metadata": state.get("metadata", {}),
            "message": state.get("message") or state.get("query") or "",
        }
        system = AGENT_SYSTEM_PROMPT
        if strict:
            system += " Return every field with the exact schema type; use null or [] instead of prose."
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

    @staticmethod
    def _complete_result(result: dict[str, Any], state: dict[str, Any]) -> AgentResult:
        completed = dict(result)
        completed.setdefault("assistant_message", completed.get("response", ""))
        completed.setdefault("response", completed.get("assistant_message", ""))
        completed.setdefault("intent", "handbook_question")
        completed.setdefault("draft", {})
        completed.setdefault("missing_fields", [])
        completed.setdefault("action", None)
        completed.setdefault("citations", [])
        completed.setdefault("error", None)
        if completed.get("intent") == "handbook_question":
            completed["citations"] = ProductionAgent._trusted_citations(state.get("handbook_results"))
        completed["workflow_id"] = state.get("workflow_id")
        completed["workflow_type"] = state.get("workflow_type") or ProductionAgent._infer_workflow_type(completed)
        completed["workflow_version"] = state.get("workflow_version")
        completed["state"] = ProductionAgent._infer_state(completed, state.get("workflow_state"))
        # IDs come only from trusted application input, never from LLM output.
        completed["attachment_ids"] = ProductionAgent._merge_ids(
            state.get("workflow_attachment_ids"), state.get("attachment_ids")
        )
        draft = dict(completed.get("draft") or {})
        action = completed.get("action")
        if isinstance(action, dict) and isinstance(action.get("payload"), dict):
            draft = {**draft, **action["payload"]}
        if isinstance(action, dict) and action.get("requires_confirmation") and not action.get("action_id"):
            action = {**action, "action_id": str(uuid4())}
            completed["action"] = action
        elif not action and completed.get("workflow_type") == "resident_ticket" and completed.get("intent") == "create_ticket" and draft:
            action = {
                "type": "create_ticket",
                "action_id": str(uuid4()),
                "requires_confirmation": True,
                "payload": draft,
            }
            completed["action"] = action
            completed["state"] = "awaiting_confirmation"
        if completed["attachment_ids"]:
            draft["attachment_ids"] = completed["attachment_ids"]
        if completed.get("workflow_type") == "manager_announcement" and not draft.get("scopes"):
            inferred_scopes = ProductionAgent._infer_announcement_scopes(str(state.get("message") or state.get("query") or ""))
            if inferred_scopes:
                draft["scopes"] = inferred_scopes
                completed["missing_fields"] = [
                    field for field in completed["missing_fields"] if field != "scopes"
                ]
        workflow_intent = completed.get("intent") in {
            "create_ticket",
            "clarification_response",
            "create_announcement",
            "announcement_edit",
            "publish_announcement",
        }
        action_payload = isinstance(action, dict) and bool(action.get("payload"))
        if draft or workflow_intent or action_payload:
            try:
                if completed["workflow_type"] == "resident_ticket":
                    draft = TicketDraft.model_validate(draft).model_dump(mode="json", exclude_none=True)
                elif completed["workflow_type"] == "manager_announcement":
                    draft = AnnouncementDraft.model_validate(draft).model_dump(mode="json", exclude_none=True)
            except PydanticValidationError as exc:
                completed["error"] = {
                    "type": "invalid_draft",
                    "fields": [error.get("loc", [])[-1] for error in exc.errors()],
                }
                completed["action"] = None
        completed["draft"] = draft
        completed["query"] = state.get("query") or state.get("message") or ""
        return completed

    @staticmethod
    def _infer_workflow_type(result: dict[str, Any]) -> str | None:
        action = result.get("action") if isinstance(result.get("action"), dict) else {}
        action_type = action.get("type")
        if action_type in {"create_ticket", "preview_ticket"} or result.get("intent") == "create_ticket":
            return "resident_ticket"
        if action_type in {
            "create_announcement_draft",
            "update_announcement",
            "publish_announcement",
            "preview_announcement",
        } or result.get("intent") in {"create_announcement", "announcement_edit", "publish_announcement"}:
            return "manager_announcement"
        return None

    @staticmethod
    def _infer_state(result: dict[str, Any], current: str | None) -> str | None:
        action = result.get("action") if isinstance(result.get("action"), dict) else {}
        action_type = action.get("type")
        if action_type == "cancelled":
            return "cancelled"
        if action_type == "publish_announcement":
            return "awaiting_publish_confirmation"
        if result.get("missing_fields"):
            return "collecting"
        if action.get("requires_confirmation"):
            return "awaiting_confirmation"
        return current or "collecting"

    @staticmethod
    def _merge_ids(*groups: Any) -> list[str]:
        values: list[str] = []
        for group in groups:
            for value in group or []:
                value = str(value)
                if value and value not in values:
                    values.append(value)
        return values

    @staticmethod
    def _trusted_citations(handbook_results: Any) -> list[dict[str, Any]]:
        citations: list[dict[str, Any]] = []
        for item in handbook_results or []:
            citation = item.get("citation") if isinstance(item, dict) else None
            if isinstance(citation, dict) and citation not in citations:
                citations.append(citation)
        return citations

    @staticmethod
    def _safe_messages(messages: Any) -> list[dict[str, Any]]:
        if not isinstance(messages, list):
            return []
        result: list[dict[str, Any]] = []
        for message in messages[-12:]:
            if not isinstance(message, dict):
                continue
            role = str(message.get("role") or "")[:30]
            raw_content = str(message.get("content") or "")[:2000]
            content = ProductionAgent._redact_text(raw_content) if role == "user" else raw_content
            result.append(
                {
                    "role": role,
                    "content": content,
                }
            )
        return result

    @staticmethod
    def _safe_handbook_results(handbook_results: Any) -> list[dict[str, Any]]:
        if not isinstance(handbook_results, list):
            return []
        results: list[dict[str, Any]] = []
        for item in handbook_results[:5]:
            if not isinstance(item, dict):
                continue
            clean_item = dict(item)
            if "content" in clean_item:
                clean_item["content"] = str(clean_item["content"])[:4000]
            elif "text" in clean_item:
                clean_item["text"] = str(clean_item["text"])[:4000]
            results.append(clean_item)
        return results

    @staticmethod
    def _redact_value(value: Any) -> Any:
        if isinstance(value, str):
            return ProductionAgent._redact_text(value)[:4000]
        if isinstance(value, dict):
            return {str(key): ProductionAgent._redact_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [ProductionAgent._redact_value(item) for item in value[:20]]
        return value

    @staticmethod
    def _redact_text(value: str) -> str:
        return sanitize_user_text(value).safe_text

    def _fallback(self, state: dict[str, Any]) -> dict[str, Any]:
        message = str(state.get("message") or state.get("query") or "").strip()
        workflow_type = state.get("workflow_type")
        workflow_state = state.get("workflow_state")
        draft = dict(state.get("workflow_draft") or {})
        pending_action = state.get("pending_action") if isinstance(state.get("pending_action"), dict) else None
        handbook_results = state.get("handbook_results") or []
        if workflow_type == "manager_announcement" or state.get("actor_role") == "management":
            if not self._looks_like_announcement(message, draft, workflow_state, pending_action):
                return self._handbook_result(handbook_results)
            return self._manager_result(message, draft, workflow_state, pending_action)
        ticket_context = (state.get("metadata") or {}).get("ticket")
        if ticket_context:
            return self._ticket_question_result(message, ticket_context)
        if workflow_type == "resident_ticket" or self._looks_like_ticket(message, draft):
            return self._ticket_result(state, message, draft, workflow_state, pending_action)
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

    @staticmethod
    def _handbook_result(handbook_results: list[dict[str, Any]]) -> dict[str, Any]:
        first = handbook_results[0] if handbook_results else {}
        answer = first.get("content") or "I could not find a reliable answer in the handbook."
        return {
            "response": answer,
            "assistant_message": answer,
            "intent": "handbook_question",
            "draft": {},
            "missing_fields": [],
            "action": None,
            "citations": [item.get("citation", {}) for item in handbook_results if item.get("citation")],
            "attachment_ids": [],
        }

    @staticmethod
    def _ticket_question_result(message: str, ticket: dict[str, Any]) -> dict[str, Any]:
        folded = ProductionAgent._fold(message)
        if any(word in folded for word in ("status", "trang thai", "ma ticket", "ticket")):
            answer = (
                f"Ticket {ticket.get('ticket_code') or ticket.get('id')} "
                f"is currently {ticket.get('status', 'unknown')}."
            )
        else:
            answer = "I can help explain the current ticket or send it to management for follow-up."
        return {
            "response": answer,
            "assistant_message": answer,
            "intent": "ticket_question",
            "draft": {},
            "missing_fields": [],
            "action": None,
            "citations": [],
            "attachment_ids": [],
        }

    @staticmethod
    def _looks_like_announcement(
        message: str,
        draft: dict[str, Any],
        workflow_state: str | None,
        pending_action: dict[str, Any] | None = None,
    ) -> bool:
        if draft or pending_action or workflow_state in {"awaiting_confirmation", "awaiting_publish_confirmation"}:
            return True
        folded = ProductionAgent._fold(message)
        return any(
            word in folded
            for word in (
                "announcement",
                "thong bao",
                "tao thong bao",
                "create announcement",
                "draft announcement",
                "soan",
                "publish",
                "phat hanh",
                "xuat ban",
                "tieu de:",
                "noi dung:",
                "scope",
                "ap dung cho",
                "all residents",
                "toan bo cu dan",
            )
        )

    def _ticket_result(
        self,
        state: dict[str, Any],
        message: str,
        draft: dict[str, Any],
        workflow_state: str | None,
        pending_action: dict[str, Any] | None,
    ) -> dict[str, Any]:
        confirmation = bool(pending_action) and self._is_confirmation(message)
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

        action_id = self._pending_id(pending_action) if confirmation else str(uuid4())
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
        confirmation = bool(pending_action) and self._is_confirmation(message)
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

        if (
            workflow_state == "awaiting_publish_confirmation"
            and pending_action
            and pending_action.get("type") == "update_announcement"
            and confirmation
        ):
            action = {
                "type": "update_announcement",
                "action_id": self._pending_id(pending_action),
                "requires_confirmation": True,
                "payload": draft,
            }
            response = "The announcement draft update is ready. Confirm the changes?"
            return {
                "response": response,
                "assistant_message": response,
                "intent": "announcement_edit",
                "draft": draft,
                "missing_fields": [],
                "action": action,
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
        if workflow_state == "awaiting_publish_confirmation" and message and not confirmation:
            action = {
                "type": "update_announcement",
                "action_id": str(uuid4()),
                "requires_confirmation": True,
                "payload": draft,
            }
            response = "The announcement draft was updated. Confirm the changes before publishing?"
            return {
                "response": response,
                "assistant_message": response,
                "intent": "announcement_edit",
                "draft": draft,
                "missing_fields": [],
                "action": action,
                "citations": [],
                "attachment_ids": [],
            }
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
            "action_id": self._pending_id(pending_action) if confirmation else str(uuid4()),
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
        folded = ProductionAgent._fold(message)
        if not draft.get("category"):
            if any(word in lower for word in ("nước", "rò rỉ", "chảy", "leak", "ống")):
                draft["category"] = "plumbing"
            elif any(word in lower for word in ("điện", "đèn", "electric", "light")):
                draft["category"] = "electrical"
            elif any(word in lower for word in ("thang máy", "elevator", "hồ bơi", "gym")):
                draft["category"] = "facility"
            else:
                draft["category"] = "maintenance"
        if draft.get("category") == "maintenance":
            if any(word in folded for word in ("nuoc", "ro ri", "chay", "ong")):
                draft["category"] = "plumbing"
            elif any(word in folded for word in ("dien", "den", "electric", "light")):
                draft["category"] = "electrical"
            elif any(word in folded for word in ("thang may", "elevator", "ho boi", "gym")):
                draft["category"] = "facility"
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
        folded = ProductionAgent._fold(message)
        title_match = re.search(r"(?:tiêu đề|title)\s*[:：]\s*(.+)", message, re.IGNORECASE)
        if title_match:
            draft["title"] = title_match.group(1).strip()[:255]
        elif not draft.get("title"):
            draft["title"] = message[:120].rstrip(".!?")
        explicit_title = re.search(
            r"(?:title|tieu de|tiêu đề|doi tieu de|đổi tiêu đề)\s*[:=]\s*(.+)",
            message,
            re.IGNORECASE,
        )
        if explicit_title:
            draft["title"] = explicit_title.group(1).strip()[:255]
        explicit_content = re.search(
            r"(?:content|noi dung|nội dung)\s*[:=]\s*(.+)",
            message,
            re.IGNORECASE,
        )
        if explicit_content:
            draft["content"] = explicit_content.group(1).strip()
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
        if "khan" in folded or "emergency" in folded:
            draft["priority"] = "urgent"
        elif "quan trong" in folded or "important" in folded:
            draft["priority"] = "important"
        if "bao tri" in folded or "maintenance" in folded:
            draft["type"] = "maintenance"
        elif "su kien" in folded or "event" in folded:
            draft["type"] = "event"
        elif "khan cap" in folded or "emergency" in folded:
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

        if not draft.get("scopes"):
            if any(text in folded for text in ("toan bo cu dan", "tat ca cu dan", "all residents")):
                draft["scopes"] = [{"scope_type": "all_residents"}]
            else:
                building_match = re.search(r"(?:toa|building)\s*([A-Za-z0-9]+)", folded, re.IGNORECASE)
                if building_match:
                    draft["scopes"] = [{"scope_type": "building", "building": building_match.group(1).upper()}]
                else:
                    project_match = re.search(r"(?:du an|project)\s*([A-Za-z0-9_-]+)", folded, re.IGNORECASE)
                    if project_match:
                        draft["scopes"] = [{"scope_type": "project", "project_code": project_match.group(1).upper()}]

        if not draft.get("scopes"):
            inferred_scopes = ProductionAgent._infer_announcement_scopes(message)
            if inferred_scopes:
                draft["scopes"] = inferred_scopes

    @staticmethod
    def _infer_announcement_scopes(message: str) -> list[dict[str, str]]:
        folded = ProductionAgent._fold(message)
        building_match = re.search(r"\b(?:toa|building)\s+([a-z0-9]+)\b", folded, re.IGNORECASE)
        if building_match:
            return [{"scope_type": "building", "building": building_match.group(1).upper()}]
        project_match = re.search(r"\b(?:du an|project)\s+([a-z0-9_-]+)\b", folded, re.IGNORECASE)
        if project_match:
            return [{"scope_type": "project", "project_code": project_match.group(1).upper()}]
        if re.search(r"\b(?:toan bo|tat ca)\s+(?:cu dan|dan cu)\b", folded) or re.search(r"\b(?:cho|den|ap dung cho)\s+(?:cu dan|dan cu)\b", folded):
            return [{"scope_type": "all_residents"}]
        return []

    @staticmethod
    def _looks_like_ticket(message: str, draft: dict[str, Any]) -> bool:
        if draft:
            return True
        lower = message.lower()
        folded = ProductionAgent._fold(message)
        if any(
            word in folded
            for word in (
                "tao ticket",
                "su co",
                "bi hong",
                "khong hoat dong",
                "ro ri",
                "chay nuoc",
                "broken",
                "leak",
                "not working",
            )
        ):
            return True
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
        folded = ProductionAgent._fold(message)
        if any(word in folded for word in ("khan", "nguy hiem", "emergency", "urgent")):
            return "urgent"
        if any(word in folded for word in ("gap", "anh huong", "high", "cao")):
            return "high"
        if any(word in lower for word in ("khẩn", "nguy hiểm", "emergency", "urgent")):
            return "urgent"
        if any(word in lower for word in ("gấp", "ảnh hưởng", "high", "cao")):
            return "high"
        return "medium"

    @staticmethod
    def _is_confirmation(message: str) -> bool:
        normalized_ascii = ProductionAgent._fold(message)
        if normalized_ascii in {
            "duoc",
            "ok",
            "okay",
            "yes",
            "co",
            "xac nhan",
            "tao di",
            "publish",
            "dang di",
            "dong y",
        }:
            return True
        normalized = re.sub(r"[^a-zA-ZÀ-ỹ0-9 ]", " ", message.lower()).strip()
        return normalized in {"được", "ok", "okay", "yes", "có", "xác nhận", "tạo đi", "publish", "đăng đi", "đồng ý"}

    @staticmethod
    def _is_cancellation(message: str) -> bool:
        normalized_ascii = ProductionAgent._fold(message)
        if any(text in normalized_ascii for text in ("huy", "cancel", "khong tao", "bo qua")):
            return True
        normalized = message.lower().strip()
        return any(text in normalized for text in ("hủy", "huỷ", "cancel", "không tạo", "bỏ qua"))

    @staticmethod
    def _mentions_publish(message: str) -> bool:
        normalized_ascii = ProductionAgent._fold(message)
        if any(text in normalized_ascii for text in ("publish", "dang", "phat hanh", "xuat ban")):
            return True
        normalized = message.lower()
        return any(text in normalized for text in ("publish", "đăng", "phát hành", "xuất bản"))

    @staticmethod
    def _pending_id(action: dict[str, Any] | None) -> str | None:
        if not action or not action.get("action_id"):
            return None
        return str(action["action_id"])

    @staticmethod
    def _fold(value: str) -> str:
        # NFD does not decompose the Vietnamese đ character, so translate it
        # before the ASCII conversion used by the deterministic extractor.
        value = value.casefold().replace("đ", "d")
        return " ".join(
            unicodedata.normalize("NFD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
            .split()
        )


class AgentRuntimeHelpers:
    @staticmethod
    def extract_location(message: str) -> str | None:
        folded = ProductionAgent._fold(message)
        match = re.search(
            r"\b(?:o|tai|vi tri|khu vuc|location|at)\b\s*[:：]?\s*([^,.!?]+)",
            folded,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()
        for phrase in (
            "phong ngu",
            "phong khach",
            "bep",
            "ban cong",
            "hanh lang",
            "thang may",
            "kitchen",
            "living room",
            "bathroom",
            "hallway",
            "balcony",
        ):
            if phrase in folded:
                return phrase
        floor_match = re.search(r"\b(?:tang|floor)\s*\d+\b", folded, re.IGNORECASE)
        if floor_match:
            return floor_match.group(0)
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


def _load_context_node(state: AgentState) -> AgentState:
    return _runtime.prepare_state(dict(state))


async def _assistant_node(state: AgentState) -> AgentState:
    result = await _runtime.ainvoke(dict(state))
    return {**state, **result}


def _merge_draft_node(state: AgentState) -> dict[str, Any]:
    return {
        "draft": state.get("draft") or {},
        "missing_fields": state.get("missing_fields") or [],
    }


def _validate_required_fields_node(state: AgentState) -> dict[str, Any]:
    missing = state.get("missing_fields") or []
    return {"missing_fields": list(dict.fromkeys(str(field) for field in missing))}


def _persist_result_node(state: AgentState) -> dict[str, Any]:
    # Persistence is owned by the backend service; this node only exposes the
    # final serializable state to the caller.
    return {"error": state.get("error")}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("load_context", _load_context_node)
    # The LLM classifies intent and extracts the workflow in one structured
    # response. The deterministic _fallback() is used only when the LLM is
    # unavailable or both structured-output attempts fail.
    graph.add_node("assistant", _assistant_node)
    graph.add_node("merge_draft", _merge_draft_node)
    graph.add_node("validate_required_fields", _validate_required_fields_node)
    graph.add_node("persist_result", _persist_result_node)
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "assistant")
    graph.add_edge("assistant", "merge_draft")
    graph.add_edge("merge_draft", "validate_required_fields")
    graph.add_edge("validate_required_fields", "persist_result")
    graph.add_edge("persist_result", END)
    return graph.compile()


agent = build_graph()


# ---------------------------------------------------------------------------
# RAG Subgraph (Resident Handbook Q&A)
# ---------------------------------------------------------------------------
from src.agents.nodes.rag_nodes import (
    fallback_node,
    format_node,
    generate_node,
    retrieve_node,
)


def should_generate(state: AgentState) -> str:
    """Route based on whether retrieval found relevant chunks."""
    if state.get("error"):
        return "fallback"
    chunks = state.get("retrieved_chunks", [])
    if not chunks:
        return "fallback"
    return "generate"


def build_rag_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("format", format_node)
    graph.add_node("fallback", fallback_node)

    # Add edges
    graph.set_entry_point("retrieve")
    graph.add_conditional_edges("retrieve", should_generate)
    graph.add_edge("generate", "format")
    graph.add_edge("format", END)
    graph.add_edge("fallback", END)

    return graph.compile()


rag_agent = build_rag_graph()

__all__ = [
    "ProductionAgent",
    "AgentRuntimeHelpers",
    "agent",
    "build_graph",
    "rag_agent",
    "build_rag_graph",
]
