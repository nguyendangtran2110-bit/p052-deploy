from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import get_actor_context, get_agent_runtime
from src.backend.application.chat.contracts import AgentRuntime, ChatCommand
from src.backend.application.chat.service import ChatService
from src.backend.domain.common.auth import ActorContext
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.chat import ChatMessageRequest, ChatMessageResponse
from src.backend.schemas.tickets import TicketResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatMessageResponse)
@router.post("/messages", response_model=ChatMessageResponse)
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
            idempotency_key=request.idempotency_key,
            attachment_ids=tuple(str(attachment_id) for attachment_id in request.attachment_ids),
        ),
        actor,
    )
    return ChatMessageResponse(
        conversation_id=outcome.conversation_id,
        response=outcome.response,
        citations=outcome.citations,
        action=outcome.action,
        ticket=TicketResponse.model_validate(outcome.ticket) if outcome.ticket else None,
    )
