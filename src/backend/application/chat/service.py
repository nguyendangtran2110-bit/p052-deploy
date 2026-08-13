from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.application.ai_workflows.service import AIWorkflowService
from src.backend.application.attachments.service import AttachmentService
from src.backend.application.chat.contracts import AgentRuntime, ChatCommand, ChatOutcome
from src.backend.application.conversations.service import ConversationService
from src.backend.application.knowledge.search import KnowledgeSearchService
from src.backend.application.realtime import build_message_event, publish_conversation_event, publish_message_payload
from src.backend.application.tickets.contracts import CreateTicketCommand
from src.backend.application.tickets.service import TicketService
from src.backend.domain.ai_workflows.enums import AIWorkflowType
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
from src.backend.infrastructure.db.models import AIWorkflow, Conversation, Message, Unit
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
        self.workflows = AIWorkflowService(session)
        self.knowledge = KnowledgeSearchService(session)

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

        workflow = await self._get_workflow_for_conversation(command, conversation, actor)
        handbook_results = await self._handbook_results(command.message, conversation)
        result = await self.agent.ainvoke(
            {
                "query": command.message,
                "message": command.message,
                "actor_role": actor.role.value,
                "actor_id": actor.actor_id or actor.resident_id,
                "resident_id": actor.resident_id,
                "metadata": metadata,
                "workflow_id": command.workflow_id,
                "workflow_version": command.workflow_version,
                "confirmed_action_id": command.confirmed_action_id,
                "workflow_type": workflow.workflow_type if workflow else None,
                "workflow_state": workflow.state if workflow else None,
                "workflow_draft": workflow.draft if workflow else {},
                "pending_action": workflow.pending_action if workflow else None,
                "workflow_attachment_ids": workflow.attachment_ids if workflow else [],
                "selected_unit_id": command.unit_id or conversation.unit_id,
                "messages": metadata["messages"],
                "handbook_results": handbook_results,
            }
        )
        if self._is_resident_workflow_result(result, command, conversation, workflow):
            outcome = await self.workflows.process_agent_result(
                conversation=conversation,
                workflow=workflow,
                actor=actor,
                workflow_type=AIWorkflowType.RESIDENT_TICKET,
                command=command,
                user_message=user_message,
                result=result,
            )
            action = outcome.action
            if (
                action
                and action.get("type") == "completed"
                and command.workflow_id is None
                and command.confirmed_action_id is None
            ):
                action = {"type": "ticket_created", **(action.get("payload") or {})}
            return ChatOutcome(
                conversation_id=outcome.conversation.id,
                response=outcome.assistant_message.content,
                analysis=str(result.get("analysis") or ""),
                citations=outcome.citations,
                action=action,
                ticket=outcome.ticket,
                workflow_id=outcome.workflow.id,
                workflow_type=outcome.workflow.workflow_type,
                state=outcome.workflow.state,
                workflow_version=outcome.workflow.version,
                draft=outcome.workflow.draft or {},
                missing_fields=outcome.workflow.missing_fields or [],
                message=outcome.assistant_message,
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
            analysis=str(result.get("analysis") or ""),
            citations=citations,
            action=action,
            ticket=ticket,
        )

    async def _handbook_results(self, message: str, conversation: Conversation) -> list[dict]:
        unit = await self.session.get(Unit, conversation.unit_id) if conversation.unit_id else None
        return await self.knowledge.search(
            message,
            project_code=unit.project_code if unit else None,
            building=unit.building if unit else None,
        )

    async def _get_workflow_for_conversation(
        self,
        command: ChatCommand,
        conversation: Conversation,
        actor: ActorContext,
    ) -> AIWorkflow | None:
        if command.workflow_id:
            workflow = await self.workflows.get_workflow(command.workflow_id, actor)
            if workflow.conversation_id != conversation.id:
                raise AuthorizationError("Workflow does not belong to this conversation")
            return workflow
        if conversation.workflow_type != AIWorkflowType.RESIDENT_TICKET.value:
            return None
        return await self.session.scalar(
            select(AIWorkflow).where(AIWorkflow.conversation_id == conversation.id)
        )

    @staticmethod
    def _is_resident_workflow_result(
        result: dict[str, Any],
        command: ChatCommand,
        conversation: Conversation,
        workflow: AIWorkflow | None,
    ) -> bool:
        if command.workflow_id or command.confirmed_action_id:
            return True
        if workflow is not None and workflow.state in {
            "collecting",
            "awaiting_confirmation",
            "failed",
            "awaiting_publish_confirmation",
        }:
            return True
        if conversation.ticket is not None:
            return False
        if result.get("workflow_type") == AIWorkflowType.RESIDENT_TICKET.value:
            return True
        if result.get("intent") in {"create_ticket", "clarification_response"}:
            action = result.get("action")
            return isinstance(action, dict) and action.get("type") in {
                "create_ticket",
                "ask_clarification",
                "preview_ticket",
                "cancelled",
            }
        return isinstance(result.get("ticket_draft"), dict) or isinstance(result.get("draft"), dict) and result.get("workflow_type") == AIWorkflowType.RESIDENT_TICKET.value

    async def _get_or_create_conversation(self, command: ChatCommand, actor: ActorContext) -> Conversation:
        if command.workflow_id:
            workflow = await self.workflows.get_workflow(command.workflow_id, actor)
            if workflow.workflow_type != AIWorkflowType.RESIDENT_TICKET.value:
                raise AuthorizationError("This workflow cannot be used by resident chat")
            conversation = await self.conversations.get(workflow.conversation_id)
            if conversation is None:
                raise NotFoundError("Workflow conversation was not found")
            if command.conversation_id and command.conversation_id != conversation.id:
                raise AuthorizationError("Workflow does not belong to this conversation")
            return conversation
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
            if conversation.conversation_type == "manager_assistant":
                raise AuthorizationError("Resident cannot access a manager assistant conversation")
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
