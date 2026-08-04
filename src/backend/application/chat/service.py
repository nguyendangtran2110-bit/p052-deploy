from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.application.chat.contracts import AgentRuntime, ChatCommand, ChatOutcome
from src.backend.application.tickets.contracts import CreateTicketCommand
from src.backend.application.tickets.service import TicketService
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import AuthenticationError, AuthorizationError, NotFoundError, ValidationError
from src.backend.domain.conversations.enums import MessageRole
from src.backend.domain.identity.enums import ActorRole
from src.backend.domain.tickets.enums import TicketPriority, TicketSource
from src.backend.infrastructure.db.base import utc_now
from src.backend.infrastructure.db.models import Conversation, Message
from src.backend.infrastructure.db.repositories import ConversationRepository, ResidentRepository


class ChatService:
    def __init__(self, session: AsyncSession, agent: AgentRuntime):
        self.session = session
        self.agent = agent
        self.conversations = ConversationRepository(session)
        self.residents = ResidentRepository(session)
        self.ticket_service = TicketService(session)

    async def send(self, command: ChatCommand, actor: ActorContext) -> ChatOutcome:
        conversation = await self._get_or_create_conversation(command, actor)
        self.session.add(
            Message(
                conversation_id=conversation.id,
                role=MessageRole.USER.value,
                content=command.message,
            )
        )
        conversation.last_message_at = utc_now()
        await self.session.flush()

        result = await self.agent.ainvoke(
            {
                "query": command.message,
                "metadata": {
                    "conversation_id": conversation.id,
                    "resident_id": actor.resident_id,
                    "unit_id": command.unit_id or conversation.unit_id,
                },
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

        self.session.add(
            Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT.value,
                content=response,
                intent=result.get("intent"),
                citations=citations,
                action_payload=action,
            )
        )
        conversation.last_message_at = utc_now()
        await self.session.commit()

        return ChatOutcome(
            conversation_id=conversation.id,
            response=response,
            citations=citations,
            action=action,
            ticket=ticket,
        )

    async def _get_or_create_conversation(self, command: ChatCommand, actor: ActorContext) -> Conversation:
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
        return None
