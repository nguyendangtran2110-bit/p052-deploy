from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.application.ai_workflows.contracts import WorkflowAgentResult, WorkflowOutcome
from src.backend.application.announcements.contracts import (
    AnnouncementScopeCommand,
    CreateAnnouncementCommand,
    UpdateAnnouncementCommand,
)
from src.backend.application.announcements.service import AnnouncementService
from src.backend.application.attachments.service import AttachmentService
from src.backend.application.chat.contracts import ChatCommand
from src.backend.application.knowledge.search import KnowledgeSearchService
from src.backend.application.realtime import (
    build_message_event,
    publish_conversation_event,
    publish_message_payload,
)
from src.backend.application.tickets.contracts import CreateTicketCommand
from src.backend.application.tickets.service import TicketService
from src.backend.domain.ai_workflows.enums import AIWorkflowActionStatus, AIWorkflowState, AIWorkflowType
from src.backend.domain.announcements.enums import AnnouncementPriority, AnnouncementScopeType, AnnouncementType
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)
from src.backend.domain.identity.enums import ActorRole, ManagementRole
from src.backend.domain.tickets.enums import TicketPriority, TicketSource
from src.backend.infrastructure.db.base import utc_now
from src.backend.infrastructure.db.models import AIWorkflow, AIWorkflowAction, Announcement, Conversation, Message, Unit
from src.backend.infrastructure.db.repositories import ConversationRepository


class TicketDraftModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    unit_id: UUID | None = None
    category: str | None = Field(default=None, min_length=1, max_length=100)
    priority: Literal["low", "medium", "high", "urgent"] | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=50000)
    location: str | None = Field(default=None, min_length=1, max_length=255)


class AnnouncementScopeModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    scope_type: Literal["all_residents", "project", "building", "unit"]
    project_code: str | None = None
    building: str | None = None
    unit_id: UUID | None = None


class AnnouncementDraftModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str | None = Field(default=None, min_length=2, max_length=255)
    content: str | None = Field(default=None, min_length=2, max_length=50000)
    type: Literal[
        "general",
        "maintenance",
        "facility",
        "regulation_update",
        "event",
        "emergency",
    ] = AnnouncementType.GENERAL.value
    priority: Literal["normal", "important", "urgent"] = AnnouncementPriority.NORMAL.value
    expires_at: datetime | None = None
    scopes: list[AnnouncementScopeModel] = Field(default_factory=list)


class AgentActionModel(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str = Field(min_length=1, max_length=80)
    action_id: UUID | None = None
    requires_confirmation: bool | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentResultModel(BaseModel):
    """Validated boundary for untrusted Agent output."""

    model_config = ConfigDict(extra="ignore")

    response: str | None = None
    assistant_message: str | None = None
    intent: str | None = None
    draft: dict[str, Any] = Field(default_factory=dict)
    ticket_draft: dict[str, Any] | None = None
    announcement_draft: dict[str, Any] | None = None
    missing_fields: list[str] = Field(default_factory=list)
    action: AgentActionModel | None = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    attachment_ids: list[UUID] = Field(default_factory=list, max_length=10)
    error: dict[str, Any] | None = None


class AIWorkflowService:
    """Backend authority for AI workflow state and side-effect actions."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversations = ConversationRepository(session)
        self.attachments = AttachmentService(session)
        self.tickets = TicketService(session)
        self.announcements = AnnouncementService(session)
        self.knowledge = KnowledgeSearchService(session)

    async def create_manager_conversation(self, actor: ActorContext) -> tuple[Conversation, AIWorkflow]:
        self._require_manager(actor)
        if not actor.actor_id:
            raise AuthenticationError("Management account identity is required")
        conversation = Conversation(
            conversation_type="manager_assistant",
            workflow_type=AIWorkflowType.MANAGER_ANNOUNCEMENT.value,
            handoff_status="bot_active",
        )
        self.session.add(conversation)
        await self.session.flush()
        workflow = self._new_workflow(conversation, AIWorkflowType.MANAGER_ANNOUNCEMENT, actor)
        self.session.add(workflow)
        await self.session.flush()
        conversation.workflow_id = workflow.id
        await self.session.commit()
        return conversation, workflow

    async def get_workflow(self, workflow_id: str, actor: ActorContext) -> AIWorkflow:
        workflow = await self.session.scalar(
            select(AIWorkflow)
            .options(
                selectinload(AIWorkflow.conversation).selectinload(Conversation.messages),
                selectinload(AIWorkflow.conversation).selectinload(Conversation.ticket),
            )
            .where(AIWorkflow.id == workflow_id)
        )
        if workflow is None:
            raise NotFoundError("AI workflow was not found")
        self._authorize_workflow(workflow, actor)
        return workflow

    async def get_conversation_workflow(self, conversation_id: str, actor: ActorContext) -> tuple[Conversation, AIWorkflow]:
        conversation = await self.conversations.get(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation was not found")
        workflow = await self.session.scalar(
            select(AIWorkflow).where(AIWorkflow.conversation_id == conversation_id)
        )
        if workflow is None:
            raise NotFoundError("AI workflow was not found")
        self._authorize_workflow(workflow, actor)
        return conversation, workflow

    async def send_manager_message(
        self,
        *,
        conversation_id: str,
        actor: ActorContext,
        command: ChatCommand,
        agent: Any,
    ) -> WorkflowOutcome:
        self._require_manager(actor)
        conversation, workflow = await self.get_conversation_workflow(conversation_id, actor)
        if conversation.conversation_type != "manager_assistant":
            raise ConflictError("Conversation is not a manager assistant conversation")

        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            author_id=actor.actor_id,
            content=command.message,
        )
        self.session.add(user_message)
        conversation.last_message_at = utc_now()
        await self.session.flush()
        await self.attachments.attach_to_message(
            command.attachment_ids,
            user_message.id,
            ticket_id=None,
            actor=actor,
        )
        messages = await self.conversations.list_messages(conversation.id)
        unit = await self.session.get(Unit, conversation.unit_id) if conversation.unit_id else None
        handbook_results = await self.knowledge.search(
            command.message,
            project_code=unit.project_code if unit else None,
            building=unit.building if unit else None,
        )
        result = await agent.ainvoke(
            {
                "query": command.message,
                "message": command.message,
                "actor_role": actor.role.value,
                "actor_id": actor.actor_id,
                "resident_id": None,
                "conversation_id": conversation.id,
                "workflow_id": workflow.id,
                "workflow_type": workflow.workflow_type,
                "workflow_version": workflow.version,
                "confirmed_action_id": command.confirmed_action_id,
                "confirm_action": command.confirm_action,
                "attachment_ids": list(command.attachment_ids),
                "workflow_attachment_ids": list(workflow.attachment_ids or []),
                "messages": [
                    {
                        "role": message.role,
                        "author_id": message.author_id,
                        "content": message.content,
                        "created_at": message.created_at.isoformat(),
                    }
                    for message in messages
                ],
                "workflow_draft": workflow.draft,
                "workflow_state": workflow.state,
                "metadata": {"conversation_type": conversation.conversation_type},
                "selected_unit_id": conversation.unit_id,
                "handbook_results": handbook_results,
            }
        )
        return await self.process_agent_result(
            conversation=conversation,
            workflow=workflow,
            actor=actor,
            workflow_type=AIWorkflowType.MANAGER_ANNOUNCEMENT,
            command=command,
            user_message=user_message,
            result=result,
        )

    async def process_agent_result(
        self,
        *,
        conversation: Conversation,
        workflow: AIWorkflow | None,
        actor: ActorContext,
        workflow_type: AIWorkflowType,
        command: ChatCommand,
        user_message: Message,
        result: dict[str, Any],
    ) -> WorkflowOutcome:
        normalized = self._normalize_result(result)
        if workflow is None:
            workflow = await self._create_workflow_for_conversation(conversation, workflow_type, actor)
        else:
            self._authorize_workflow(workflow, actor)
            if workflow.workflow_type != workflow_type.value:
                raise ConflictError("Workflow type does not match this assistant")

        completed_action = await self._validate_confirmation(command, workflow)
        replaying_action = completed_action is not None
        if not replaying_action:
            self._check_version(workflow, command.workflow_version)
            if workflow.state in {
                AIWorkflowState.COMPLETED.value,
                AIWorkflowState.PUBLISHED.value,
                AIWorkflowState.CANCELLED.value,
            }:
                raise ConflictError("This AI workflow is already finished; start a new workflow")
            if workflow.state in {
                AIWorkflowState.EXECUTING.value,
                AIWorkflowState.PUBLISHING.value,
            }:
                raise ConflictError("This AI workflow action is already being processed")
        requested_attachment_ids = self._merge_ids(command.attachment_ids)
        await self.attachments.bind_to_workflow(requested_attachment_ids, workflow.id, actor)
        merged_draft = self._merge_draft(workflow.draft or {}, normalized.draft, normalized.action)
        if workflow_type is AIWorkflowType.RESIDENT_TICKET and command.unit_id:
            merged_draft.setdefault("unit_id", command.unit_id)
        if workflow_type is AIWorkflowType.RESIDENT_TICKET and not merged_draft.get("priority"):
            merged_draft["priority"] = TicketPriority.MEDIUM.value
        attachment_ids = self._merge_ids(workflow.attachment_ids or [], requested_attachment_ids)
        workflow.attachment_ids = attachment_ids

        pending_action = workflow.pending_action if isinstance(workflow.pending_action, dict) else None
        candidate_action = normalized.action or pending_action
        read_only_result = normalized.intent in {"handbook_question", "ticket_question"} and normalized.action is None
        if completed_action is not None:
            candidate_action = {
                "type": completed_action.action_type,
                "action_id": command.confirmed_action_id,
                "requires_confirmation": True,
                "payload": completed_action.response_payload or {},
            }
        if (
            candidate_action
            and pending_action
            and command.confirmed_action_id
            and command.confirmed_action_id == str(pending_action.get("action_id"))
            and (
                candidate_action.get("type") == pending_action.get("type")
                or candidate_action.get("type")
                in {"create_ticket", "create_announcement_draft", "update_announcement", "publish_announcement"}
            )
        ):
            candidate_action = {**candidate_action, "action_id": pending_action["action_id"]}
        action = None if read_only_result else self._normalize_action(candidate_action, workflow_type, merged_draft)
        missing_fields = [] if read_only_result else self._required_missing(workflow_type, merged_draft)
        if normalized.missing_fields and not read_only_result:
            missing_fields = self._merge_missing(
                missing_fields,
                [field for field in normalized.missing_fields if field in missing_fields],
            )
        if normalized.error:
            error_fields = [str(field) for field in normalized.error.get("fields", []) if field]
            workflow.state = AIWorkflowState.COLLECTING.value
            workflow.pending_action = None
            workflow.last_error = {"type": str(normalized.error.get("type") or "agent_error")}
            action = {
                "type": "ask_clarification",
                "action_id": self._action_id(pending_action),
                "requires_confirmation": False,
                "payload": {"fields": error_fields},
            }
            if error_fields:
                missing_fields = self._merge_missing(missing_fields, error_fields)
        elif action and action.get("type") == "cancelled":
            workflow.state = AIWorkflowState.CANCELLED.value
            workflow.pending_action = None
            workflow.last_error = None
            missing_fields = []
        elif missing_fields:
            workflow.state = AIWorkflowState.COLLECTING.value
            workflow.pending_action = action if action and action.get("type") == "ask_clarification" else None
            action = {
                "type": "ask_clarification",
                "action_id": self._action_id(action),
                "requires_confirmation": False,
                "payload": {"fields": missing_fields},
            }
        elif (
            workflow_type is AIWorkflowType.MANAGER_ANNOUNCEMENT
            and self._has_created_announcement(workflow)
            and not replaying_action
        ):
            action = self._normalize_manager_follow_up_action(action, merged_draft, workflow)

        confirmed = self._is_confirmed(command, workflow, action)
        side_effect_action = action and action.get("type") in {
            "create_ticket",
            "create_announcement_draft",
            "update_announcement",
            "publish_announcement",
        }
        domain_ticket = None
        domain_announcement = None
        execution_error: Exception | None = None
        if side_effect_action and confirmed and not missing_fields:
            workflow.state = (
                AIWorkflowState.PUBLISHING.value
                if action.get("type") == "publish_announcement"
                else AIWorkflowState.EXECUTING.value
            )
            await self._reserve_action_state(workflow)
            try:
                domain_ticket, domain_announcement, action = await self._execute_action(
                    workflow=workflow,
                    action=action,
                    actor=actor,
                    workflow_type=workflow_type,
                    command=command,
                    draft=merged_draft,
                )
            except DomainError:
                raise
            except Exception as exc:
                execution_error = exc
                workflow.state = AIWorkflowState.FAILED.value
                workflow.last_error = {"type": type(exc).__name__, "message": str(exc)}
                action = {
                    **action,
                    "type": "action_failed",
                    "requires_confirmation": True,
                    "payload": {"error": "The action could not be completed."},
                }
        elif workflow.state != AIWorkflowState.CANCELLED.value:
            if workflow_type is AIWorkflowType.MANAGER_ANNOUNCEMENT and self._has_created_announcement(workflow):
                workflow.state = AIWorkflowState.AWAITING_PUBLISH_CONFIRMATION.value
            elif missing_fields:
                workflow.state = AIWorkflowState.COLLECTING.value
            elif action and action.get("requires_confirmation"):
                workflow.state = AIWorkflowState.AWAITING_CONFIRMATION.value
            else:
                workflow.state = AIWorkflowState.COLLECTING.value

        workflow.draft = merged_draft
        workflow.missing_fields = missing_fields
        if not replaying_action and not read_only_result:
            workflow.pending_action = action if action and action.get("requires_confirmation") else None
        if execution_error is None and normalized.error is None and workflow.state != AIWorkflowState.FAILED.value:
            workflow.last_error = None
        if domain_ticket is not None:
            workflow.result = {"ticket_id": domain_ticket.id, "ticket_code": domain_ticket.ticket_code}
            workflow.state = AIWorkflowState.COMPLETED.value
            workflow.completed_at = utc_now()
        if domain_announcement is not None:
            workflow.result = {
                "announcement_id": domain_announcement.id,
                "announcement_code": domain_announcement.announcement_code,
                "announcement_version": domain_announcement.version,
            }
            if action and action.get("type") == "published":
                workflow.state = AIWorkflowState.PUBLISHED.value
                workflow.completed_at = utc_now()
                workflow.pending_action = None
            elif replaying_action and workflow.pending_action:
                workflow.state = AIWorkflowState.AWAITING_PUBLISH_CONFIRMATION.value
                if action:
                    action = {**action, "next_action": workflow.pending_action}
            else:
                workflow.state = AIWorkflowState.AWAITING_PUBLISH_CONFIRMATION.value
                publish_action = {
                    "type": "publish_announcement",
                    "action_id": str(uuid4()),
                    "requires_confirmation": True,
                    "payload": {
                        "announcement_id": domain_announcement.id,
                        "announcement_version": domain_announcement.version,
                    },
                }
                workflow.pending_action = publish_action
                if action:
                    action = {**action, "next_action": publish_action}

        expected_version = workflow.version
        workflow.version += 1
        user_message.workflow_id = workflow.id
        user_message.workflow_state = workflow.state
        user_message.workflow_version = workflow.version
        assistant_content = (
            "Không thể hoàn tất thao tác lúc này. Vui lòng xác nhận lại để thử lại."
            if execution_error is not None
            else normalized.response or self._default_response(workflow_type, workflow.state, missing_fields)
        )
        assistant = Message(
            conversation_id=conversation.id,
            role="assistant",
            author_id=actor.actor_id or actor.resident_id,
            content=assistant_content,
            intent=normalized.intent,
            citations=normalized.citations,
            action_payload=action,
            workflow_id=workflow.id,
            workflow_state=workflow.state,
            workflow_version=workflow.version,
        )
        self.session.add(assistant)
        conversation.last_message_at = utc_now()
        conversation.workflow_id = workflow.id
        conversation.workflow_type = workflow.workflow_type
        await self._save_workflow(workflow, expected_version)
        await self.session.flush()
        await self.session.commit()
        await self.session.refresh(workflow)

        user_event = build_message_event(user_message, conversation, attachment_ids=command.attachment_ids)
        assistant_event = build_message_event(assistant, conversation)
        publish_message_payload(conversation, user_event, include_management=workflow_type is AIWorkflowType.MANAGER_ANNOUNCEMENT)
        publish_message_payload(conversation, assistant_event, include_management=workflow_type is AIWorkflowType.MANAGER_ANNOUNCEMENT)
        if domain_ticket is not None or domain_announcement is not None:
            publish_conversation_event(
                conversation,
                "conversation.workflow.changed",
                {"workflow_id": workflow.id, "state": workflow.state, "workflow_version": workflow.version},
            )
        return WorkflowOutcome(
            workflow=workflow,
            conversation=conversation,
            assistant_message=assistant,
            action=action,
            ticket=domain_ticket,
            announcement=domain_announcement,
            citations=normalized.citations,
        )

    async def cancel(self, workflow_id: str, actor: ActorContext) -> AIWorkflow:
        workflow = await self.get_workflow(workflow_id, actor)
        if workflow.state in {
            AIWorkflowState.COMPLETED.value,
            AIWorkflowState.PUBLISHED.value,
            AIWorkflowState.CANCELLED.value,
        }:
            return workflow
        workflow.state = AIWorkflowState.CANCELLED.value
        workflow.pending_action = None
        expected_version = workflow.version
        workflow.version += 1
        await self._save_workflow(workflow, expected_version)
        await self.session.commit()
        return workflow

    async def _save_workflow(self, workflow: AIWorkflow, expected_version: int) -> None:
        with self.session.no_autoflush:
            result = await self.session.execute(
                update(AIWorkflow)
                .where(AIWorkflow.id == workflow.id, AIWorkflow.version == expected_version)
                .values(
                    state=workflow.state,
                    version=workflow.version,
                    draft=workflow.draft,
                    missing_fields=workflow.missing_fields,
                    pending_action=workflow.pending_action,
                    attachment_ids=workflow.attachment_ids,
                    result=workflow.result,
                    last_error=workflow.last_error,
                    completed_at=workflow.completed_at,
                    updated_at=utc_now(),
                )
                .execution_options(synchronize_session=False)
            )
        if result.rowcount != 1:
            raise ConflictError("AI workflow has changed; reload it before continuing")

    async def _reserve_action_state(self, workflow: AIWorkflow) -> None:
        """Reserve the current workflow version before a domain service commits.

        Ticket and announcement services own their existing transactions. The
        conditional update prevents a second request with the same stale
        workflow version from reaching those side effects first.
        """
        expected_version = workflow.version
        next_version = expected_version + 1
        result = await self.session.execute(
            update(AIWorkflow)
            .where(AIWorkflow.id == workflow.id, AIWorkflow.version == expected_version)
            .values(state=workflow.state, version=next_version, updated_at=utc_now())
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            raise ConflictError("AI workflow has changed; reload it before continuing")
        workflow.version = next_version

    async def _execute_action(
        self,
        *,
        workflow: AIWorkflow,
        action: dict[str, Any],
        actor: ActorContext,
        workflow_type: AIWorkflowType,
        command: ChatCommand,
        draft: dict[str, Any],
    ) -> tuple[Any | None, Any | None, dict[str, Any]]:
        action_id = self._action_id(action)
        action_type = str(action.get("type"))
        existing = await self.session.scalar(
            select(AIWorkflowAction).with_for_update().where(
                AIWorkflowAction.workflow_id == workflow.id,
                AIWorkflowAction.action_id == action_id,
            )
        )
        if existing is not None:
            if existing.status == AIWorkflowActionStatus.SUCCEEDED.value:
                return await self._replay_action(existing, actor)
            if existing.status in {
                AIWorkflowActionStatus.PENDING.value,
                AIWorkflowActionStatus.EXECUTING.value,
                AIWorkflowActionStatus.UNKNOWN.value,
            }:
                raise ConflictError("This action is already being processed; reload the workflow")
            if existing.status == AIWorkflowActionStatus.FAILED.value and not (
                command.confirm_action or command.confirmed_action_id
            ):
                raise ConflictError("The previous action failed; confirm again to retry")

        allowed_actions = {
            AIWorkflowType.RESIDENT_TICKET: {"create_ticket"},
            AIWorkflowType.MANAGER_ANNOUNCEMENT: {
                "create_announcement_draft",
                "update_announcement",
                "publish_announcement",
            },
        }
        if action_type not in allowed_actions[workflow_type]:
            raise AuthorizationError("This action is not allowed for the current workflow")

        ledger = existing or AIWorkflowAction(
            workflow_id=workflow.id,
            action_id=action_id,
            action_type=action_type,
            workflow_version=workflow.version,
            status=AIWorkflowActionStatus.PENDING.value,
            request_payload={"type": action_type, "payload": self._redact_payload(action.get("payload") or {})},
        )
        if existing is None:
            self.session.add(ledger)
        ledger.status = AIWorkflowActionStatus.EXECUTING.value
        await self.session.flush()

        try:
            ticket = None
            announcement = None
            if action_type == "create_ticket":
                ticket = await self._create_ticket(workflow, draft, actor, command, action_id)
                response = {"ticket_id": ticket.id, "ticket_code": ticket.ticket_code}
                final_action = {"type": "completed", "action_id": action_id, "requires_confirmation": False, "payload": response}
            elif action_type in {"create_announcement_draft", "update_announcement"}:
                announcement = await self._upsert_announcement(workflow, draft, actor, action_type)
                response = {
                    "announcement_id": announcement.id,
                    "announcement_code": announcement.announcement_code,
                    "announcement_version": announcement.version,
                }
                final_action = {
                    "type": "announcement_draft_created",
                    "action_id": action_id,
                    "requires_confirmation": False,
                    "payload": response,
                }
            elif action_type == "publish_announcement":
                announcement = await self._publish_announcement(workflow, actor)
                response = {
                    "announcement_id": announcement.id,
                    "announcement_code": announcement.announcement_code,
                    "announcement_version": announcement.version,
                }
                final_action = {"type": "published", "action_id": action_id, "requires_confirmation": False, "payload": response}
            else:
                raise ValidationError(f"Unsupported AI action: {action_type}")

            ledger.status = AIWorkflowActionStatus.SUCCEEDED.value
            ledger.response_payload = response
            ledger.completed_at = utc_now()
            await self.session.flush()
            return ticket, announcement, final_action
        except Exception as exc:
            ledger.status = AIWorkflowActionStatus.FAILED.value
            ledger.error_payload = {"message": str(exc), "type": type(exc).__name__}
            ledger.completed_at = utc_now()
            await self.session.flush()
            raise

    async def _replay_action(self, action: AIWorkflowAction, actor: ActorContext) -> tuple[Any | None, Any | None, dict[str, Any]]:
        payload = action.response_payload or {}
        if action.action_type == "create_ticket":
            ticket_id = payload.get("ticket_id")
            if not ticket_id:
                raise ConflictError("Completed ticket action has no result")
            ticket = await self.tickets.get(ticket_id, actor)
            return ticket, None, {"type": "completed", "action_id": action.action_id, "requires_confirmation": False, "payload": payload}
        announcement_id = payload.get("announcement_id")
        if not announcement_id:
            raise ConflictError("Completed announcement action has no result")
        announcement = await self.announcements.get_management(announcement_id, actor)
        final_type = "published" if action.action_type == "publish_announcement" else "announcement_draft_created"
        return None, announcement, {"type": final_type, "action_id": action.action_id, "requires_confirmation": False, "payload": payload}

    async def _create_ticket(
        self, workflow: AIWorkflow, draft: dict[str, Any], actor: ActorContext, command: ChatCommand, action_id: str
    ) -> Any:
        if actor.role is not ActorRole.RESIDENT or not actor.resident_id:
            raise AuthenticationError("Resident authentication is required to create a ticket")
        try:
            values = TicketDraftModel.model_validate(draft)
        except PydanticValidationError as exc:
            raise ValidationError(f"Invalid ticket draft: {exc.errors()[0]['msg']}") from exc
        if any(getattr(values, field) in {None, ""} for field in ("unit_id", "category", "title", "description", "location")):
            raise ValidationError("Ticket draft is missing required fields")
        try:
            priority = TicketPriority(str(values.priority or TicketPriority.MEDIUM.value).lower())
        except ValueError as exc:
            raise ValidationError("Ticket priority is invalid") from exc
        return await self.tickets.create(
            CreateTicketCommand(
                resident_id=actor.resident_id,
                unit_id=str(values.unit_id),
                category=str(values.category).strip(),
                priority=priority,
                title=str(values.title).strip(),
                description=str(values.description).strip(),
                location=str(values.location).strip(),
                source=TicketSource.CHAT,
                conversation_id=workflow.conversation_id,
                idempotency_key=action_id or command.idempotency_key,
                attachment_ids=tuple(workflow.attachment_ids or []),
            ),
            actor,
        )

    async def _upsert_announcement(
        self, workflow: AIWorkflow, draft: dict[str, Any], actor: ActorContext, action_type: str
    ) -> Announcement:
        self._require_manager(actor)
        try:
            values = AnnouncementDraftModel.model_validate(draft)
        except PydanticValidationError as exc:
            raise ValidationError(f"Invalid announcement draft: {exc.errors()[0]['msg']}") from exc
        scopes = self._scope_commands(values.scopes)
        if not values.title or not values.content:
            raise ValidationError("Announcement draft is missing title or content")
        if action_type == "update_announcement" and workflow.result and workflow.result.get("announcement_id"):
            announcement_id = str(workflow.result["announcement_id"])
            current = await self.announcements.get_management(announcement_id, actor)
            changed = {"title", "content", "type", "priority", "expires_at", "scopes", "attachment_ids"}
            return await self.announcements.update(
                announcement_id,
                UpdateAnnouncementCommand(
                    version=current.version,
                    changed_fields=frozenset(changed),
                    title=values.title,
                    content=values.content,
                    announcement_type=AnnouncementType(values.type),
                    priority=AnnouncementPriority(values.priority),
                    expires_at=values.expires_at,
                    scopes=scopes,
                    attachment_ids=tuple(workflow.attachment_ids or []),
                ),
                actor,
            )
        return await self.announcements.create(
            CreateAnnouncementCommand(
                title=values.title,
                content=values.content,
                announcement_type=AnnouncementType(values.type),
                priority=AnnouncementPriority(values.priority),
                expires_at=values.expires_at,
                scopes=scopes,
                attachment_ids=tuple(workflow.attachment_ids or []),
            ),
            actor,
        )

    async def _publish_announcement(self, workflow: AIWorkflow, actor: ActorContext) -> Announcement:
        self._require_manager(actor)
        announcement_id = str((workflow.result or {}).get("announcement_id") or workflow.draft.get("announcement_id") or "")
        if not announcement_id:
            raise ValidationError("No announcement draft is available to publish")
        expected_version = (workflow.result or {}).get("announcement_version")
        pending_action = workflow.pending_action if isinstance(workflow.pending_action, dict) else None
        pending_payload = pending_action.get("payload") if pending_action else None
        if isinstance(pending_payload, dict) and pending_payload.get("announcement_version") is not None:
            expected_version = pending_payload["announcement_version"]
        if expected_version is None:
            raise ValidationError("Announcement version is missing from the workflow")
        try:
            expected_version = int(expected_version)
        except (TypeError, ValueError) as exc:
            raise ValidationError("Announcement version is invalid") from exc
        announcement = await self.announcements.get_management(announcement_id, actor)
        return await self.announcements.publish(announcement.id, expected_version, actor)

    async def _create_workflow_for_conversation(
        self, conversation: Conversation, workflow_type: AIWorkflowType, actor: ActorContext
    ) -> AIWorkflow:
        if workflow_type is AIWorkflowType.RESIDENT_TICKET:
            if actor.role is not ActorRole.RESIDENT or not actor.resident_id:
                raise AuthenticationError("Resident authentication is required for a ticket workflow")
        else:
            self._require_manager(actor)
        existing = await self.session.scalar(
            select(AIWorkflow).where(AIWorkflow.conversation_id == conversation.id)
        )
        if existing:
            return existing
        workflow = self._new_workflow(conversation, workflow_type, actor)
        self.session.add(workflow)
        await self.session.flush()
        conversation.workflow_id = workflow.id
        conversation.workflow_type = workflow_type.value
        return workflow

    @staticmethod
    def _new_workflow(conversation: Conversation, workflow_type: AIWorkflowType, actor: ActorContext) -> AIWorkflow:
        return AIWorkflow(
            conversation_id=conversation.id,
            workflow_type=workflow_type.value,
            owner_actor_id=actor.actor_id or actor.resident_id or "anonymous",
            owner_resident_id=actor.resident_id if workflow_type is AIWorkflowType.RESIDENT_TICKET else None,
            state=AIWorkflowState.COLLECTING.value,
            version=0,
        )

    @staticmethod
    def _normalize_result(result: dict[str, Any]) -> WorkflowAgentResult:
        if not isinstance(result, dict):
            raise ValidationError("Agent returned an invalid result")
        try:
            validated = AgentResultModel.model_validate(result)
        except PydanticValidationError as exc:
            raise ValidationError("Agent returned an invalid structured result") from exc
        action = validated.action.model_dump(mode="json") if validated.action else None
        draft = dict(validated.draft)
        for legacy_draft in (validated.ticket_draft, validated.announcement_draft):
            if legacy_draft:
                draft = {**draft, **legacy_draft}
        if action and isinstance(action.get("payload"), dict):
            draft = {**draft, **action["payload"]}
        return WorkflowAgentResult(
            response=validated.assistant_message or validated.response or "",
            intent=validated.intent,
            draft={key: value for key, value in draft.items() if value is not None},
            missing_fields=list(validated.missing_fields),
            action=action,
            citations=list(validated.citations),
            attachment_ids=[str(value) for value in validated.attachment_ids],
            error=validated.error,
        )

    @staticmethod
    def _merge_draft(current: dict[str, Any], incoming: dict[str, Any], action: dict[str, Any] | None) -> dict[str, Any]:
        merged = dict(current)
        for key, value in incoming.items():
            if value is not None and value != "":
                merged[key] = value
        if action and isinstance(action.get("payload"), dict):
            for key, value in action["payload"].items():
                if value is not None and value != "":
                    merged[key] = value
        return merged

    @staticmethod
    def _required_missing(workflow_type: AIWorkflowType, draft: dict[str, Any]) -> list[str]:
        fields = ("unit_id", "category", "priority", "title", "description", "location") if workflow_type is AIWorkflowType.RESIDENT_TICKET else ("title", "content", "scopes")
        missing: list[str] = []
        for field in fields:
            value = draft.get(field)
            if field == "scopes":
                if not isinstance(value, list) or not value:
                    missing.append(field)
            elif value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field)
        return missing

    @staticmethod
    def _normalize_action(action: dict[str, Any] | None, workflow_type: AIWorkflowType, draft: dict[str, Any]) -> dict[str, Any] | None:
        if action is None:
            if not AIWorkflowService._required_missing(workflow_type, draft):
                action = {
                    "type": "create_ticket" if workflow_type is AIWorkflowType.RESIDENT_TICKET else "create_announcement_draft",
                    "requires_confirmation": True,
                    "payload": draft,
                }
            else:
                return None
        normalized = dict(action)
        normalized["action_id"] = str(normalized.get("action_id") or uuid4())
        if normalized.get("requires_confirmation") is None:
            normalized["requires_confirmation"] = normalized.get("type") in {
                "create_ticket", "create_announcement_draft", "update_announcement", "publish_announcement"
            }
        normalized.setdefault("payload", draft)
        return normalized

    @staticmethod
    def _normalize_manager_follow_up_action(action: dict[str, Any] | None, draft: dict[str, Any], workflow: AIWorkflow) -> dict[str, Any]:
        if action and action.get("type") in {"publish_announcement", "update_announcement"}:
            return action
        return {
            "type": "publish_announcement",
            "action_id": str(uuid4()),
            "requires_confirmation": True,
            "payload": {"announcement_id": (workflow.result or {}).get("announcement_id")},
        }

    @staticmethod
    def _has_created_announcement(workflow: AIWorkflow) -> bool:
        return bool(workflow.result and workflow.result.get("announcement_id"))

    @staticmethod
    def _is_confirmed(command: ChatCommand, workflow: AIWorkflow, action: dict[str, Any] | None) -> bool:
        if not action or not action.get("requires_confirmation"):
            return False
        if command.confirmed_action_id:
            return command.confirmed_action_id == str(action.get("action_id"))
        # Legacy clients sent only confirm_action. Keep this compatibility path
        # until all clients send action_id explicitly.
        return (
            command.confirm_action
            and command.workflow_id is None
            and workflow.workflow_type == AIWorkflowType.RESIDENT_TICKET.value
            and (workflow.pending_action is not None or workflow.version == 0)
        )

    @staticmethod
    def _check_version(workflow: AIWorkflow, expected_version: int | None) -> None:
        if expected_version is not None and workflow.version != expected_version:
            raise ConflictError("AI workflow has changed; reload it before continuing")

    async def _validate_confirmation(
        self, command: ChatCommand, workflow: AIWorkflow
    ) -> AIWorkflowAction | None:
        if not command.confirmed_action_id:
            return None
        if command.workflow_id != str(workflow.id):
            raise ConflictError("Confirmation must reference the current workflow")
        if command.workflow_version is None:
            raise ConflictError("Confirmation must include the current workflow version")
        completed_action = await self.session.scalar(
            select(AIWorkflowAction).where(
                AIWorkflowAction.workflow_id == workflow.id,
                AIWorkflowAction.action_id == command.confirmed_action_id,
                AIWorkflowAction.status == AIWorkflowActionStatus.SUCCEEDED.value,
            )
        )
        if completed_action is not None:
            return completed_action
        pending_action = workflow.pending_action if isinstance(workflow.pending_action, dict) else None
        if pending_action is None or str(pending_action.get("action_id")) != command.confirmed_action_id:
            raise ConflictError("Confirmation action is stale; reload the workflow")
        return None

    @staticmethod
    def _merge_ids(*groups: Any) -> list[str]:
        result: list[str] = []
        for group in groups:
            for value in group or []:
                value = str(value)
                if value not in result:
                    result.append(value)
        return result

    @staticmethod
    def _merge_missing(*groups: list[str]) -> list[str]:
        result: list[str] = []
        for group in groups:
            for value in group:
                if value not in result:
                    result.append(value)
        return result

    @staticmethod
    def _action_id(action: dict[str, Any] | None) -> str:
        if not action:
            return str(uuid4())
        action_id = action.get("action_id")
        return str(action_id or uuid4())

    @staticmethod
    def _scope_commands(scopes: list[AnnouncementScopeModel]) -> tuple[AnnouncementScopeCommand, ...]:
        result: list[AnnouncementScopeCommand] = []
        for scope in scopes:
            try:
                scope_type = AnnouncementScopeType(scope.scope_type)
            except ValueError as exc:
                raise ValidationError("Announcement scope type is invalid") from exc
            result.append(
                AnnouncementScopeCommand(
                    scope_type=scope_type,
                    project_code=scope.project_code,
                    building=scope.building,
                    unit_id=str(scope.unit_id) if scope.unit_id else None,
                )
            )
        return tuple(result)

    @staticmethod
    def _redact_payload(payload: dict[str, Any]) -> dict[str, Any]:
        redacted = dict(payload)
        for key in ("access_token", "refresh_token", "upload_url", "download_url"):
            if key in redacted:
                redacted[key] = "[redacted]"
        return redacted

    @staticmethod
    def _default_response(workflow_type: AIWorkflowType, state: str, missing_fields: list[str]) -> str:
        if missing_fields:
            return "Vui lòng cung cấp thêm: " + ", ".join(missing_fields) + "."
        if state == AIWorkflowState.AWAITING_CONFIRMATION.value:
            return "Thông tin đã đủ. Bạn có muốn thực hiện thao tác này không?"
        if workflow_type is AIWorkflowType.MANAGER_ANNOUNCEMENT:
            return "Bản nháp thông báo đã được tạo. Vui lòng xác nhận nếu muốn publish."
        return "Ticket đã được tạo thành công."

    @staticmethod
    def _authorize_workflow(workflow: AIWorkflow, actor: ActorContext) -> None:
        if workflow.workflow_type == AIWorkflowType.RESIDENT_TICKET.value:
            if actor.role is not ActorRole.RESIDENT or workflow.owner_resident_id != actor.resident_id:
                raise AuthorizationError("Actor cannot access this resident workflow")
            return
        if not actor.is_management or actor.management_role not in {ManagementRole.MANAGER, ManagementRole.ADMIN}:
            raise AuthorizationError("Manager or administrator permission is required")
        if actor.management_role is not ManagementRole.ADMIN and workflow.owner_actor_id != actor.actor_id:
            raise AuthorizationError("Manager can only access their own announcement workflow")

    @staticmethod
    def _require_manager(actor: ActorContext) -> None:
        if not actor.is_management or actor.management_role not in {ManagementRole.MANAGER, ManagementRole.ADMIN}:
            raise AuthorizationError("Manager or administrator permission is required")
