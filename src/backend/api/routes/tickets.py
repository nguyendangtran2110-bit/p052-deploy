from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import get_actor_context, require_resident
from src.backend.application.tickets.contracts import CreateTicketCommand
from src.backend.application.tickets.service import TicketService
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.tickets.enums import TicketPriority, TicketSource, TicketStatus
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.tickets import (
    TicketCreate,
    TicketListResponse,
    TicketResponse,
    TicketStatusUpdate,
    TicketSummaryResponse,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request: TicketCreate,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=100)] = None,
    session: AsyncSession = Depends(get_db_session),
    actor: ActorContext = Depends(require_resident),
) -> TicketResponse:
    ticket = await TicketService(session).create(
        CreateTicketCommand(
            resident_id=str(actor.resident_id),
            unit_id=str(request.unit_id),
            category=request.category,
            priority=request.priority,
            title=request.title,
            description=request.description,
            location=request.location,
            source=TicketSource.FORM,
            idempotency_key=idempotency_key,
        ),
        actor,
    )
    return TicketResponse.model_validate(ticket)


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    ticket_status: TicketStatus | None = Query(default=None, alias="status"),
    source: TicketSource | None = None,
    priority: TicketPriority | None = None,
    assigned_to_id: UUID | None = None,
    resident_id: UUID | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    actor: ActorContext = Depends(get_actor_context),
) -> TicketListResponse:
    items, total = await TicketService(session).list(
        actor,
        status=ticket_status,
        source=source.value if source else None,
        priority=priority,
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


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    actor: ActorContext = Depends(get_actor_context),
) -> TicketResponse:
    ticket = await TicketService(session).get(str(ticket_id), actor)
    return TicketResponse.model_validate(ticket)


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
async def update_ticket_status(
    ticket_id: UUID,
    request: TicketStatusUpdate,
    session: AsyncSession = Depends(get_db_session),
    actor: ActorContext = Depends(get_actor_context),
) -> TicketResponse:
    ticket = await TicketService(session).transition(str(ticket_id), request.status, actor, request.comment)
    return TicketResponse.model_validate(ticket)
