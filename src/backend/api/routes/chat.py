import json
import logging
import re
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import get_actor_context, get_agent_runtime
from src.backend.application.chat.contracts import AgentRuntime, ChatCommand
from src.backend.application.chat.service import ChatService
from src.backend.core.config import get_settings
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import AuthenticationError
from src.backend.domain.identity.enums import ActorRole
from src.backend.infrastructure.db.session import SessionFactory, get_db_session
from src.backend.schemas.chat import ChatMessageRequest, ChatMessageResponse
from src.backend.schemas.tickets import TicketResponse
from src.backend.security.chat_guardrails import sanitize_model_output, sanitize_user_text
from src.services.groq_llm import stream_rag_answer
from src.services.rag import retrieve_context

logger = logging.getLogger(__name__)


def _message_payload(message) -> dict:
    return {
        "id": message.id,
        "role": message.role,
        "author_id": message.author_id,
        "content": message.content,
        "intent": message.intent,
        "citations": message.citations,
        "action_payload": message.action_payload,
        "workflow_id": message.workflow_id,
        "workflow_state": message.workflow_state,
        "workflow_version": message.workflow_version,
        "attachment_ids": [attachment.id for attachment in message.__dict__.get("attachments", [])],
        "created_at": message.created_at,
    }

router = APIRouter(prefix="/chat", tags=["chat"])


class _StreamedRagAgent:
    def __init__(self, answer: str, citations: list[dict]) -> None:
        self.answer = answer
        self.citations = citations

    async def ainvoke(self, _state: dict) -> dict:
        return {
            "response": self.answer,
            "assistant_message": self.answer,
            "intent": "handbook_question",
            "citations": self.citations,
            "draft": {},
            "missing_fields": [],
            "action": None,
        }


def _wants_stream(request: Request, command: ChatMessageRequest) -> bool:
    accept = request.headers.get("accept", "")
    ticket_language = re.compile(
        r"ticket|sự cố|hỏng|rò rỉ|sửa chữa|bảo trì|maintenance|broken|leak|repair",
        re.IGNORECASE,
    )
    return (
        "text/event-stream" in accept
        and not command.confirm_action
        and command.workflow_id is None
        and command.ticket_id is None
        and not command.attachment_ids
        and not ticket_language.search(command.message)
    )


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"


async def _stream_rag_message(
    request: ChatMessageRequest,
    actor: ActorContext,
) -> AsyncIterator[str]:
    """Stream RAG output, then persist the completed assistant response."""
    try:
        safe_query = sanitize_user_text(request.message).safe_text
        chunks = [chunk.to_dict() for chunk in retrieve_context(safe_query, top_k=5)]
        citations = [
            {
                "title": chunk.get("source_file", ""),
                "section": chunk.get("section_title", ""),
                "page": chunk.get("page_number") or None,
            }
            for chunk in chunks
        ]

        answer_parts: list[str] = []
        if chunks:
            # Buffer the provider stream so no unreviewed model text reaches the
            # client. SSE framing is retained for frontend compatibility.
            for token in stream_rag_answer(safe_query, chunks, []):
                answer_parts.append(token)
        else:
            answer_parts.append(
                "Thông tin hiện có chưa đủ để xác định chính xác câu trả lời. "
                "Vui lòng liên hệ Ban Quản Lý tòa nhà để được hỗ trợ."
            )
            yield _sse({"type": "token", "content": answer_parts[0]})

        answer = sanitize_model_output(
            "".join(answer_parts), max_chars=get_settings().chat_output_max_chars
        )
        for offset in range(0, len(answer), 160):
            yield _sse({"type": "token", "content": answer[offset : offset + 160]})
        # Streaming continues after FastAPI has released request-scoped
        # dependencies, so persistence must use a fresh session.
        async with SessionFactory() as persist_session:
            outcome = await ChatService(
                persist_session,
                _StreamedRagAgent(answer, citations),
            ).send(
                ChatCommand(
                    message=request.message,
                    conversation_id=str(request.conversation_id) if request.conversation_id else None,
                    unit_id=str(request.unit_id) if request.unit_id else None,
                    idempotency_key=request.idempotency_key,
                ),
                actor,
            )
            # Materialize ORM-backed fields while the persistence session is
            # still active. The stream itself may outlive request dependencies.
            done_payload = {
                "type": "done",
                "conversation_id": outcome.conversation_id,
                "response": answer,
                "citations": citations,
                "message": _message_payload(outcome.message) if outcome.message else None,
            }
        yield _sse(done_payload)
    except Exception:
        logger.exception("Guarded RAG stream failed")
        yield _sse({"type": "error", "message": "Không thể hoàn tất phản hồi lúc này. Vui lòng thử lại sau."})


@router.post("", response_model=ChatMessageResponse, response_model_exclude_none=True)
@router.post("/messages", response_model=ChatMessageResponse, response_model_exclude_none=True)
async def send_message(
    request: ChatMessageRequest,
    http_request: Request,
    session: AsyncSession = Depends(get_db_session),
    actor: ActorContext = Depends(get_actor_context),
    agent: AgentRuntime = Depends(get_agent_runtime),
) -> ChatMessageResponse | StreamingResponse:
    settings = get_settings()
    sanitize_user_text(request.message)
    if actor.role is ActorRole.ANONYMOUS and not settings.chat_allow_anonymous:
        raise AuthenticationError("Authentication is required to use chatbot")
    if _wants_stream(http_request, request):
        return StreamingResponse(
            _stream_rag_message(request, actor),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    outcome = await ChatService(session, agent).send(
        ChatCommand(
            message=request.message,
            conversation_id=str(request.conversation_id) if request.conversation_id else None,
            ticket_id=str(request.ticket_id) if request.ticket_id else None,
            unit_id=str(request.unit_id) if request.unit_id else None,
            confirm_action=request.confirm_action,
            workflow_id=str(request.workflow_id) if request.workflow_id else None,
            workflow_version=request.workflow_version,
            confirmed_action_id=str(request.confirmed_action_id) if request.confirmed_action_id else None,
            idempotency_key=request.idempotency_key,
            attachment_ids=tuple(str(attachment_id) for attachment_id in request.attachment_ids),
        ),
        actor,
    )
    return ChatMessageResponse(
        conversation_id=outcome.conversation_id,
        response=outcome.response,
        analysis=outcome.analysis or None,
        citations=outcome.citations,
        action=outcome.action,
        ticket=TicketResponse.model_validate(outcome.ticket) if outcome.ticket else None,
        workflow_id=outcome.workflow_id,
        workflow_type=outcome.workflow_type,
        state=outcome.state,
        workflow_version=outcome.workflow_version,
        draft=outcome.draft,
        missing_fields=outcome.missing_fields,
        message=_message_payload(outcome.message) if outcome.message else None,
    )
