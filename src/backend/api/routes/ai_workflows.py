from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import get_actor_context, get_agent_runtime, require_manager_or_admin
from src.backend.application.ai_workflows.service import AIWorkflowService
from src.backend.application.chat.contracts import AgentRuntime, ChatCommand
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import NotFoundError
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.ai_workflows import (
    AIWorkflowCancelResponse,
    AIWorkflowConversationCreateRequest,
    AIWorkflowConversationResponse,
    AIWorkflowMessageRequest,
    AIWorkflowMessageResponse,
    AIWorkflowResponse,
)
from src.backend.schemas.announcements import AnnouncementResponse
from src.backend.schemas.tickets import TicketResponse

router = APIRouter(prefix="/management/assistant", tags=["management-assistant"])
workflow_router = APIRouter(prefix="/ai/workflows", tags=["ai-workflows"])


def _message_response(message) -> AIWorkflowMessageResponse:
    return AIWorkflowMessageResponse(
        id=message.id,
        role=message.role,
        author_id=message.author_id,
        content=message.content,
        intent=message.intent,
        citations=message.citations or [],
        action_payload=message.action_payload,
        workflow_id=message.workflow_id,
        workflow_state=message.workflow_state,
        workflow_version=message.workflow_version,
        attachment_ids=[attachment.id for attachment in message.__dict__.get("attachments", [])],
        created_at=message.created_at,
    )


async def _domain_objects(workflow, actor, session):
    ticket = None
    announcement = None
    result = workflow.result or {}
    if result.get("ticket_id"):
        from src.backend.application.tickets.service import TicketService

        ticket = await TicketService(session).get(str(result["ticket_id"]), actor)
    if result.get("announcement_id"):
        from src.backend.application.announcements.service import AnnouncementService

        announcement = await AnnouncementService(session).get_management(str(result["announcement_id"]), actor)
    return ticket, announcement


async def _workflow_response(workflow, actor, session, *, message=None, action=None, citations=None):
    ticket, announcement = await _domain_objects(workflow, actor, session)
    return AIWorkflowResponse(
        conversation_id=workflow.conversation_id,
        workflow_id=workflow.id,
        workflow_type=workflow.workflow_type,
        state=workflow.state,
        workflow_version=workflow.version,
        message=_message_response(message) if message else None,
        draft=workflow.draft or {},
        missing_fields=workflow.missing_fields or [],
        action=action or workflow.pending_action,
        citations=citations or [],
        ticket=TicketResponse.model_validate(ticket) if ticket else None,
        announcement=AnnouncementResponse.model_validate(announcement) if announcement else None,
        error=workflow.last_error,
    )


@router.post("/conversations", response_model=AIWorkflowConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_manager_assistant_conversation(
    _payload: AIWorkflowConversationCreateRequest | None = None,
    actor: ActorContext = Depends(require_manager_or_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AIWorkflowConversationResponse:
    conversation, workflow = await AIWorkflowService(session).create_manager_conversation(actor)
    return AIWorkflowConversationResponse(
        conversation_id=conversation.id,
        workflow_id=workflow.id,
        workflow_type=workflow.workflow_type,
        state=workflow.state,
        workflow_version=workflow.version,
        messages=[],
        draft=workflow.draft,
        missing_fields=workflow.missing_fields,
    )


@router.get("/conversations/{conversation_id}", response_model=AIWorkflowConversationResponse)
async def get_manager_assistant_conversation(
    conversation_id: UUID,
    actor: ActorContext = Depends(require_manager_or_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AIWorkflowConversationResponse:
    conversation, workflow = await AIWorkflowService(session).get_conversation_workflow(str(conversation_id), actor)
    if conversation.conversation_type != "manager_assistant":
        raise NotFoundError("Manager assistant conversation was not found")
    ticket, announcement = await _domain_objects(workflow, actor, session)
    return AIWorkflowConversationResponse(
        conversation_id=conversation.id,
        workflow_id=workflow.id,
        workflow_type=workflow.workflow_type,
        state=workflow.state,
        workflow_version=workflow.version,
        messages=[_message_response(message) for message in conversation.messages],
        draft=workflow.draft or {},
        missing_fields=workflow.missing_fields or [],
        action=workflow.pending_action,
        ticket=TicketResponse.model_validate(ticket) if ticket else None,
        announcement=AnnouncementResponse.model_validate(announcement) if announcement else None,
        error=workflow.last_error,
    )


@router.post("/conversations/{conversation_id}/messages", response_model=AIWorkflowResponse)
async def send_manager_assistant_message(
    conversation_id: UUID,
    request: AIWorkflowMessageRequest,
    actor: ActorContext = Depends(require_manager_or_admin),
    agent: AgentRuntime = Depends(get_agent_runtime),
    session: AsyncSession = Depends(get_db_session),
) -> AIWorkflowResponse:
    outcome = await AIWorkflowService(session).send_manager_message(
        conversation_id=str(conversation_id),
        actor=actor,
        command=ChatCommand(
            message=request.message,
            conversation_id=str(conversation_id),
            workflow_id=str(request.workflow_id) if request.workflow_id else None,
            workflow_version=request.workflow_version,
            confirmed_action_id=str(request.confirmed_action_id) if request.confirmed_action_id else None,
            confirm_action=request.confirm_action,
            idempotency_key=request.idempotency_key,
            attachment_ids=tuple(str(attachment_id) for attachment_id in request.attachment_ids),
        ),
        agent=agent,
    )
    return await _workflow_response(
        outcome.workflow,
        actor,
        session,
        message=outcome.assistant_message,
        action=outcome.action,
        citations=outcome.citations,
    )


@workflow_router.get("/{workflow_id}", response_model=AIWorkflowResponse)
async def get_ai_workflow(
    workflow_id: UUID,
    actor: ActorContext = Depends(get_actor_context),
    session: AsyncSession = Depends(get_db_session),
) -> AIWorkflowResponse:
    workflow = await AIWorkflowService(session).get_workflow(str(workflow_id), actor)
    return await _workflow_response(workflow, actor, session)


@workflow_router.post("/{workflow_id}/cancel", response_model=AIWorkflowCancelResponse)
async def cancel_ai_workflow(
    workflow_id: UUID,
    actor: ActorContext = Depends(get_actor_context),
    session: AsyncSession = Depends(get_db_session),
) -> AIWorkflowCancelResponse:
    workflow = await AIWorkflowService(session).cancel(str(workflow_id), actor)
    return AIWorkflowCancelResponse(
        workflow_id=workflow.id,
        state=workflow.state,
        workflow_version=workflow.version,
    )
