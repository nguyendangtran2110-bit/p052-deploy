"""Compatibility endpoints for the original deterministic MVP API.

The modular backend is the primary API, but the first implementation exposed
the handbook demo and ticket-draft flow at these paths. Keeping these routes
lets existing clients and regression tests continue to work during the
migration.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import get_actor_context
from src.backend.application.tickets.service import TicketService
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.conversations.enums import ConversationHandoffStatus
from src.backend.domain.tickets.enums import TicketPriority, TicketSource, TicketStatus
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.tickets import TicketListResponse, TicketSummaryResponse
from src.models.schemas import (
    DemoChatRequest,
    DraftRequest,
    ManagerActionRequest,
    SubmitDraftRequest,
    TicketUpdateRequest,
)
from src.services.mvp import mvp_service

router = APIRouter(tags=["legacy-demo"])


@router.post("/chat/query")
async def demo_chat(request: DemoChatRequest):
    """Return the deterministic handbook answer or a ticket-draft proposal."""
    detection = mvp_service.detect(request.message)
    if detection and request.actor_role == "resident":
        preview = mvp_service.preview_draft(request.message, detection)
        return {
            "answer": "Mình nhận thấy bạn đang báo một vấn đề có thể cần ban quản lý xử lý. Bạn có muốn tạo ticket không?",
            "notification": {"kind": "ticket_draft_available", "severity": detection["priority"]},
            "draft_preview": preview,
        }
    lowered = request.message.casefold()
    if "hồ bơi" in lowered or "pool" in lowered:
        return {
            "answer": "Hồ bơi mở cửa hàng ngày từ 06:00 đến 21:00.",
            "citation": "Resident Handbook · Section 4.2",
        }
    return {"answer": "Mình chưa tìm thấy thông tin đó trong tài liệu demo hiện có.", "citation": None}


@router.post("/ticket-drafts")
async def create_ticket_draft(request: DraftRequest):
    if request.actor_role != "resident":
        raise HTTPException(status_code=403, detail="Only residents can create ticket drafts")
    try:
        return mvp_service.create_draft(request.message)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/ticket-drafts/{draft_id}")
async def get_ticket_draft(draft_id: str):
    draft = mvp_service.get_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Ticket draft not found")
    return draft


@router.post("/ticket-drafts/{draft_id}/submit")
async def submit_ticket_draft(draft_id: str, request: SubmitDraftRequest):
    try:
        return {"ticket": mvp_service.submit_draft(draft_id, request.actor_role)}
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


def _uses_modular_ticket_contract(request: Request) -> bool:
    """Detect authenticated modular-API callers without changing legacy calls."""
    return any(
        request.headers.get(header)
        for header in ("authorization", "x-actor-role", "x-actor-id", "x-resident-id", "x-management-role")
    ) or bool(request.query_params.get("access_token"))


@router.get("/tickets", include_in_schema=False)
async def list_tickets_compat(
    request: Request,
    ticket_status: TicketStatus | None = Query(default=None, alias="status"),
    source: TicketSource | None = None,
    priority: TicketPriority | None = None,
    handoff_status: ConversationHandoffStatus | None = Query(default=None),
    assigned_to_id: UUID | None = None,
    resident_id: UUID | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    actor: ActorContext = Depends(get_actor_context),
):
    """Serve legacy in-memory tickets for old callers and DB tickets for new ones."""
    if not _uses_modular_ticket_contract(request):
        return {"tickets": mvp_service.tickets()}

    items, total = await TicketService(session).list(
        actor,
        status=ticket_status,
        source=source.value if source else None,
        priority=priority,
        handoff_status=handoff_status,
        assigned_to_id=str(assigned_to_id) if assigned_to_id else None,
        resident_id=str(resident_id) if resident_id else None,
        offset=offset,
        limit=limit,
    )
    return TicketListResponse(
        items=[TicketSummaryResponse.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.patch("/tickets/{ticket_id}")
async def update_legacy_ticket(ticket_id: str, request: TicketUpdateRequest):
    try:
        return mvp_service.update_ticket(
            ticket_id,
            request.actor_role,
            request.status,
            request.note,
            request.assigned_manager,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/tickets/{ticket_id}/contact-resident")
async def contact_legacy_ticket_resident(ticket_id: str, request: ManagerActionRequest):
    try:
        return mvp_service.contact_resident(ticket_id, request.actor_role)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
