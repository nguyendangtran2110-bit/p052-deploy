from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.application.attachments.service import AttachmentService
from src.backend.application.realtime import build_message_event, publish_conversation_event, publish_message_payload
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import AuthorizationError, ConflictError, NotFoundError
from src.backend.domain.conversations.enums import ConversationHandoffStatus, MessageRole
from src.backend.infrastructure.db.base import utc_now
from src.backend.infrastructure.db.models import Conversation, Message
from src.backend.infrastructure.db.repositories import ConversationRepository


class ConversationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversations = ConversationRepository(session)
        self.attachments = AttachmentService(session)

    async def get(self, conversation_id: str, actor: ActorContext) -> Conversation:
        conversation = await self.conversations.get(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation was not found")
        self._authorize_read(conversation, actor)
        return conversation

    async def list_resident_support(
        self,
        actor: ActorContext,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        if actor.role.value != "resident" or not actor.resident_id:
            raise AuthorizationError("Resident permission is required")
        return await self.conversations.list_resident_support(
            actor.resident_id,
            offset=offset,
            limit=limit,
        )

    async def list_handoffs(
        self,
        actor: ActorContext,
        *,
        handoff_status: ConversationHandoffStatus = ConversationHandoffStatus.WAITING_MANAGEMENT,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Conversation], int]:
        if not actor.is_management:
            raise AuthorizationError("Management permission is required")
        return await self.conversations.list_handoffs(
            handoff_status=handoff_status.value,
            offset=offset,
            limit=limit,
        )

    async def add_management_message(
        self,
        conversation_id: str,
        content: str,
        actor: ActorContext,
        *,
        expected_version: int | None,
        attachment_ids: tuple[str, ...] = (),
    ) -> tuple[Conversation, Message]:
        if not actor.is_management:
            raise AuthorizationError("Management permission is required")
        if not actor.actor_id:
            raise AuthorizationError("A manager identity is required to send a conversation message")
        conversation = await self.conversations.get(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation was not found")
        if conversation.status != "active":
            raise ConflictError("Conversation is closed")
        version = conversation.conversation_version if expected_version is None else expected_version
        assigned = await self.conversations.assign_for_management_message(
            conversation.id,
            actor.actor_id,
            expected_version=version,
        )
        if not assigned:
            await self.session.refresh(conversation)
            if conversation.assigned_manager_id and conversation.assigned_manager_id != actor.actor_id:
                raise ConflictError("Conversation is assigned to another manager")
            raise ConflictError("Conversation changed; reload it before replying")
        await self.session.refresh(conversation)

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.MANAGEMENT.value,
            author_id=actor.actor_id,
            content=content,
            intent="management_reply",
        )
        self.session.add(message)
        await self.session.flush()
        await self.attachments.attach_to_message(
            attachment_ids,
            message.id,
            ticket_id=(conversation.__dict__.get("ticket").id if conversation.__dict__.get("ticket") else None),
            actor=actor,
        )
        message_event = build_message_event(message, conversation, attachment_ids=attachment_ids)
        conversation.handoff_status = ConversationHandoffStatus.MANAGEMENT_ACTIVE.value
        conversation.last_message_at = utc_now()
        await self.session.commit()
        publish_message_payload(conversation, message_event)
        return conversation, message

    async def handoff_to_bot(
        self,
        conversation_id: str,
        actor: ActorContext,
        *,
        expected_version: int | None,
        note: str | None = None,
    ) -> tuple[Conversation, Message]:
        if not actor.is_management:
            raise AuthorizationError("Management permission is required")
        if not actor.actor_id:
            raise AuthorizationError("A manager identity is required to return a conversation to the chatbot")
        conversation = await self.conversations.get(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation was not found")
        if conversation.status != "active":
            raise ConflictError("Conversation is closed")
        if conversation.assigned_manager_id != actor.actor_id and not actor.is_management_admin:
            raise ConflictError("Conversation must be assigned to this manager before handback")

        previous_status = conversation.handoff_status
        normalized_note = note.strip() if note and note.strip() else None
        action_payload: dict[str, Any] = {
            "from_status": previous_status,
            "to_status": ConversationHandoffStatus.BOT_ACTIVE.value,
        }
        if normalized_note:
            action_payload["note"] = normalized_note

        released = await self.conversations.release_assignment(
            conversation.id,
            actor.actor_id,
            expected_version=expected_version,
            is_admin=actor.is_management_admin,
        )
        if not released:
            await self.session.refresh(conversation)
            if conversation.assigned_manager_id != actor.actor_id and not actor.is_management_admin:
                raise ConflictError("Conversation is assigned to another manager")
            raise ConflictError("Conversation changed; reload it before handing back")
        await self.session.refresh(conversation)
        conversation.last_message_at = utc_now()
        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.SYSTEM.value,
            author_id=actor.actor_id,
            content="Management returned this conversation to the chatbot.",
            intent="management_handoff_to_bot",
            action_payload=action_payload,
        )
        self.session.add(message)
        await self.session.flush()
        message_event = build_message_event(message, conversation)
        await self.session.commit()
        publish_message_payload(conversation, message_event)
        publish_conversation_event(
            conversation,
            "conversation.handoff.changed",
            {"handoff_status": conversation.handoff_status, "assigned_manager_id": conversation.assigned_manager_id},
        )
        return conversation, message

    async def take_over(
        self,
        conversation_id: str,
        actor: ActorContext,
        *,
        expected_version: int,
        note: str | None = None,
    ) -> tuple[Conversation, Message]:
        self._require_management(actor)
        if not actor.actor_id:
            raise AuthorizationError("A manager identity is required to take over a conversation")
        conversation = await self.conversations.get(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation was not found")
        if conversation.status != "active":
            raise ConflictError("Conversation is closed")

        previous_owner = conversation.assigned_manager_id
        taken_over = await self.conversations.take_over(
            conversation.id,
            actor.actor_id,
            expected_version=expected_version,
        )
        if not taken_over:
            await self.session.refresh(conversation)
            raise ConflictError("Conversation changed; reload it before taking over")
        await self.session.refresh(conversation)

        action_payload: dict[str, Any] = {
            "from_assigned_manager_id": previous_owner,
            "to_assigned_manager_id": actor.actor_id,
        }
        normalized_note = note.strip() if note and note.strip() else None
        if normalized_note:
            action_payload["note"] = normalized_note
        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.SYSTEM.value,
            author_id=actor.actor_id,
            content="Management reassigned this conversation for follow-up.",
            intent="management_takeover",
            action_payload=action_payload,
        )
        self.session.add(message)
        await self.session.flush()
        message_event = build_message_event(message, conversation)
        conversation.last_message_at = utc_now()
        await self.session.commit()
        publish_message_payload(conversation, message_event)
        publish_conversation_event(
            conversation,
            "conversation.assignment.changed",
            {"assigned_manager_id": conversation.assigned_manager_id},
        )
        return conversation, message

    @staticmethod
    def _require_management(actor: ActorContext) -> None:
        if not actor.is_management:
            raise AuthorizationError("Management permission is required")

    def mark_handoff(
        self,
        conversation: Conversation,
        *,
        requester_id: str | None,
        action: dict[str, Any] | None,
    ) -> Message | None:
        if conversation.status != "active":
            raise ConflictError("Conversation is closed")
        if conversation.handoff_status == ConversationHandoffStatus.MANAGEMENT_ACTIVE.value:
            return None

        conversation.handoff_status = ConversationHandoffStatus.WAITING_MANAGEMENT.value
        conversation.handoff_requested_at = utc_now()
        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.SYSTEM.value,
            author_id=requester_id,
            content="The resident conversation has been handed off to management.",
            intent="handoff_requested",
            action_payload=action,
        )
        self.session.add(message)
        return message

    def add_handoff_acknowledgement(self, conversation: Conversation, *, requester_id: str | None) -> Message:
        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.SYSTEM.value,
            author_id=requester_id,
            content="The message was delivered to management for follow-up.",
            intent="handoff_message_received",
            action_payload={"handoff_status": conversation.handoff_status},
        )
        self.session.add(message)
        return message

    @staticmethod
    def _authorize_read(conversation: Conversation, actor: ActorContext) -> None:
        if actor.is_management:
            return
        if actor.role.value == "resident" and actor.resident_id == conversation.resident_id:
            return
        if not actor.is_authenticated:
            raise AuthorizationError("Authentication is required to access this conversation")
        raise AuthorizationError("Actor cannot access this conversation")
