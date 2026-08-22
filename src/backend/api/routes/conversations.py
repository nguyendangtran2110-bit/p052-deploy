from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import get_actor_context, require_resident
from src.backend.application.conversations.service import ConversationService
from src.backend.domain.common.auth import ActorContext
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.conversations import (
    ConversationMessageResponse,
    ConversationResponse,
    ResidentConversationListResponse,
    ResidentConversationSummaryResponse,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=ResidentConversationListResponse)
async def list_resident_conversations(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    actor: ActorContext = Depends(require_resident),
) -> ResidentConversationListResponse:
    items, total = await ConversationService(session).list_resident_support(
        actor,
        offset=offset,
        limit=limit,
    )
    return ResidentConversationListResponse(
        items=[
            ResidentConversationSummaryResponse(
                conversation_id=item["conversation"].id,
                unit_id=item["conversation"].unit_id,
                status=item["conversation"].status,
                handoff_status=item["conversation"].handoff_status,
                assigned_manager_id=item["conversation"].assigned_manager_id,
                conversation_version=item["conversation"].conversation_version,
                last_message_at=item["conversation"].last_message_at,
                last_message_role=item["last_message_role"],
                last_message_preview=item["last_message_preview"],
                message_count=item["message_count"],
            )
            for item in items
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


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
