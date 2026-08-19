from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import get_actor_context, get_agent_runtime
from src.backend.application.chat.contracts import AgentRuntime, ChatCommand
from src.backend.application.chat.service import ChatService
from src.backend.domain.common.auth import ActorContext
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.chat import ChatMessageRequest, ChatMessageResponse
from src.backend.schemas.tickets import TicketResponse


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


@router.post("", response_model=ChatMessageResponse, response_model_exclude_none=True)
@router.post("/messages", response_model=ChatMessageResponse, response_model_exclude_none=True)
async def send_message(
    request: ChatMessageRequest,
    session: AsyncSession = Depends(get_db_session),
    actor: ActorContext = Depends(get_actor_context),
    agent: AgentRuntime = Depends(get_agent_runtime),
) -> ChatMessageResponse:
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
