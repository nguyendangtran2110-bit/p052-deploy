from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import get_actor_context
from src.backend.application.conversations.service import ConversationService
from src.backend.domain.common.auth import ActorContext
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.conversations import ConversationMessageResponse, ConversationResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    actor: ActorContext = Depends(get_actor_context),
) -> ConversationResponse:
    conversation = await ConversationService(session).get(str(conversation_id), actor)
    return ConversationResponse(
        conversation_id=conversation.id,
        resident_id=conversation.resident_id,
        unit_id=conversation.unit_id,
        status=conversation.status,
        handoff_status=conversation.handoff_status,
        handoff_requested_at=conversation.handoff_requested_at,
        assigned_manager_id=conversation.assigned_manager_id,
        conversation_version=conversation.conversation_version,
        last_message_at=conversation.last_message_at,
        ticket=conversation.ticket,
        messages=[ConversationMessageResponse.model_validate(message) for message in conversation.messages],
    )
