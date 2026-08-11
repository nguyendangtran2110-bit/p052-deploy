from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.application.attachments.service import AttachmentService
from src.backend.application.chat.contracts import AgentRuntime, ChatCommand, ChatOutcome
from src.backend.application.conversations.service import ConversationService
from src.backend.application.realtime import build_message_event, publish_conversation_event, publish_message_payload
from src.backend.application.tickets.contracts import CreateTicketCommand
from src.backend.application.tickets.service import TicketService
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.backend.domain.conversations.enums import ConversationHandoffStatus, MessageRole
from src.backend.domain.identity.enums import ActorRole
from src.backend.domain.tickets.enums import TicketPriority, TicketSource
from src.backend.infrastructure.db.base import utc_now
from src.backend.infrastructure.db.models import Conversation, Message
from src.backend.infrastructure.db.repositories import ConversationRepository, ResidentRepository

HANDOFF_ACTION_TYPES = {"handoff_to_management", "escalate_to_management", "request_management"}


class ChatService:
    def __init__(self, session: AsyncSession, agent: AgentRuntime):
        self.session = session
        self.agent = agent
        self.conversations = ConversationRepository(session)
        self.conversation_service = ConversationService(session)
        self.residents = ResidentRepository(session)
        self.ticket_service = TicketService(session)
        self.attachments = AttachmentService(session)

    async def send(self, command: ChatCommand, actor: ActorContext) -> ChatOutcome:
        conversation = await self._get_or_create_conversation(command, actor)
        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER.value,
            author_id=actor.resident_id or actor.actor_id,
            content=command.message,
        )
        self.session.add(user_message)
        conversation.last_message_at = utc_now()
        await self.session.flush()
        await self.attachments.attach_to_message(
            command.attachment_ids,
            user_message.id,
            ticket_id=conversation.ticket.id if conversation.ticket else None,
            actor=actor,
        )
        user_event = build_message_event(user_message, conversation, attachment_ids=command.attachment_ids)

        if conversation.handoff_status != ConversationHandoffStatus.BOT_ACTIVE.value:
            acknowledgement = self.conversation_service.add_handoff_acknowledgement(
                conversation,
                requester_id=actor.resident_id or actor.actor_id,
            )
            await self.session.flush()
            acknowledgement_event = build_message_event(acknowledgement, conversation)
            conversation.last_message_at = utc_now()
            await self.conversations.bump_version(conversation.id)
            await self.session.refresh(conversation)
            await self.session.commit()
            publish_message_payload(conversation, user_event, include_management=True)
            publish_message_payload(conversation, acknowledgement_event, include_management=True)
            return ChatOutcome(
                conversation_id=conversation.id,
                response="Your message has been sent to management for follow-up.",
                action={
                    "type": "handoff_pending",
                    "handoff_status": conversation.handoff_status,
                },
            )

        ticket = conversation.ticket
        messages = await self.conversations.list_messages(conversation.id)
        metadata = {
            "conversation_id": conversation.id,
            "resident_id": actor.resident_id,
            "unit_id": command.unit_id or conversation.unit_id,
            "handoff_status": conversation.handoff_status,
            "messages": [
                {
                    "role": message.role,
                    "author_id": message.author_id,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                }
                for message in messages
            ],
        }
        if ticket:
            metadata["ticket"] = {
                "id": ticket.id,
                "ticket_code": ticket.ticket_code,
                "status": ticket.status,
                "category": ticket.category,
                "priority": ticket.priority,
                "title": ticket.title,
                "description": ticket.description,
                "location": ticket.location,
            }

        result = await self.agent.ainvoke(
            {
                "query": command.message,
                "metadata": metadata,
            }
        )
        response = str(result.get("response") or "")
        citations = self._normalize_citations(result.get("citations"))
        action = self._normalize_action(result)
        ticket = None

        if command.confirm_action and action and action.get("type") in {"confirm_ticket", "create_ticket"}:
            ticket = await self._create_ticket_from_action(action, command, conversation, actor)
            action = {"type": "ticket_created", "ticket_id": ticket.id, "ticket_code": ticket.ticket_code}
        elif action and action.get("type") == "create_ticket":
            action = {**action, "type": "confirm_ticket"}

        assistant_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT.value,
            content=response,
            intent=result.get("intent"),
            citations=citations,
            action_payload=action,
        )
        self.session.add(assistant_message)
        await self.session.flush()
        assistant_event = build_message_event(assistant_message, conversation)
        handoff_message = None
        if action and action.get("type") in HANDOFF_ACTION_TYPES:
            handoff_message = self.conversation_service.mark_handoff(
                conversation,
                requester_id=actor.resident_id or actor.actor_id,
                action=action,
            )
            action = {
                **action,
                "type": "handoff_requested",
                "handoff_status": ConversationHandoffStatus.WAITING_MANAGEMENT.value,
            }
        await self.session.flush()
        handoff_event = build_message_event(handoff_message, conversation) if handoff_message else None
        conversation.last_message_at = utc_now()
        await self.conversations.bump_version(conversation.id)
        await self.session.refresh(conversation)
        await self.session.commit()
        notify_management = conversation.__dict__.get("ticket") is not None or handoff_event is not None
        publish_message_payload(conversation, user_event, include_management=notify_management)
        publish_message_payload(conversation, assistant_event, include_management=notify_management)
        if handoff_event is not None:
            publish_message_payload(conversation, handoff_event, include_management=True)
            publish_conversation_event(
                conversation,
                "conversation.handoff.changed",
                {"handoff_status": conversation.handoff_status, "assigned_manager_id": conversation.assigned_manager_id},
            )

        return ChatOutcome(
            conversation_id=conversation.id,
            response=response,
            citations=citations,
            action=action,
            ticket=ticket,
        )

    async def _get_or_create_conversation(self, command: ChatCommand, actor: ActorContext) -> Conversation:
        if command.ticket_id:
            if actor.role is not ActorRole.RESIDENT or not actor.resident_id:
                raise AuthenticationError("Resident authentication is required to use a ticket conversation")
            ticket, conversation = await self.ticket_service.get_conversation(command.ticket_id, actor)
            if command.conversation_id and command.conversation_id != conversation.id:
                raise AuthorizationError("Conversation does not belong to this ticket")
            if ticket.resident_id != actor.resident_id:
                raise AuthorizationError("Actor cannot access this ticket conversation")
            return conversation

        if command.conversation_id:
            conversation = await self.conversations.get(command.conversation_id)
            if conversation is None:
                raise NotFoundError("Conversation was not found")
            if conversation.resident_id and conversation.resident_id != actor.resident_id:
                raise AuthorizationError("Actor cannot access this conversation")
            return conversation

        if command.unit_id:
            if actor.role is not ActorRole.RESIDENT or not actor.resident_id:
                raise AuthenticationError("Resident authentication is required to use unit context")
            if not await self.residents.has_active_unit(actor.resident_id, command.unit_id):
                raise AuthorizationError("Resident does not have access to the selected unit")

        conversation = Conversation(
            resident_id=actor.resident_id,
            unit_id=command.unit_id,
            ticket=None,
        )
        await self.conversations.add(conversation)
        return conversation

    async def _create_ticket_from_action(
        self,
        action: dict[str, Any],
        chat_command: ChatCommand,
        conversation: Conversation,
        actor: ActorContext,
    ):
        if actor.role is not ActorRole.RESIDENT or not actor.resident_id:
            raise AuthenticationError("Resident authentication is required to confirm a ticket")
        if conversation.ticket is not None:
            raise ConflictError("This conversation is already linked to a ticket")

        payload = action.get("payload") or {}
        unit_id = str(payload.get("unit_id") or chat_command.unit_id or conversation.unit_id or "")
        required = ("category", "description", "location")
        missing = [field for field in required if not str(payload.get(field) or "").strip()]
        if not unit_id:
            missing.append("unit_id")
        if missing:
            raise ValidationError(f"Agent ticket payload is missing required fields: {', '.join(missing)}")

        priority_value = str(payload.get("priority") or TicketPriority.MEDIUM.value).lower()
        try:
            priority = TicketPriority(priority_value)
        except ValueError:
            priority = TicketPriority.MEDIUM

        return await self.ticket_service.create(
            CreateTicketCommand(
                resident_id=actor.resident_id,
                unit_id=unit_id,
                category=str(payload["category"]).strip(),
                priority=priority,
                title=str(payload.get("title") or payload["category"]).strip(),
                description=str(payload["description"]).strip(),
                location=str(payload["location"]).strip(),
                source=TicketSource.CHAT,
                conversation_id=conversation.id,
                idempotency_key=chat_command.idempotency_key,
                attachment_ids=chat_command.attachment_ids,
            ),
            actor,
        )

    @staticmethod
    def _normalize_citations(value: Any) -> list[dict[str, Any]]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]

    @staticmethod
    def _normalize_action(result: dict[str, Any]) -> dict[str, Any] | None:
        action = result.get("action")
        if isinstance(action, dict) and isinstance(action.get("type"), str):
            return action
        draft = result.get("ticket_draft")
        if isinstance(draft, dict):
            return {"type": "confirm_ticket", "payload": draft}
        if result.get("handoff_to_management") is True or result.get("needs_management") is True:
            return {
                "type": "handoff_to_management",
                "payload": result.get("handoff_payload") or {},
            }
        return None
