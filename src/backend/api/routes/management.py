from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import require_management, require_management_admin
from src.backend.application.auth.contracts import ManagementRegistrationCommand
from src.backend.application.auth.service import AuthService
from src.backend.application.management.contracts import UpdateManagementAccountCommand, UpdateResidentCommand
from src.backend.application.management.service import ManagementService
from src.backend.application.tickets.service import TicketService
from src.backend.core.config import Settings, get_settings
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.identity.enums import AccountStatus, ManagementRole
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.auth import AccountResponse
from src.backend.schemas.management import (
    ManagementAccountCreateRequest,
    ManagementAccountListResponse,
    ManagementAccountUpdateRequest,
    ManagementDashboardResponse,
    ManagementResidentListResponse,
    ManagementResidentResponse,
    ManagementResidentUpdateRequest,
    TicketAssignmentRequest,
)
from src.backend.schemas.residents import ResidentResponse, ResidentUnitSummary, UnitResponse
from src.backend.schemas.tickets import TicketResponse

router = APIRouter(prefix="/management", tags=["management"])


def _resident_response(resident) -> ManagementResidentResponse:
    return ManagementResidentResponse(
        **ResidentResponse.model_validate(resident).model_dump(),
        account=AccountResponse.model_validate(resident.account) if resident.account else None,
        units=[
            ResidentUnitSummary(
                **UnitResponse.model_validate(link.unit).model_dump(),
                resident_role=link.role,
                is_primary=link.is_primary,
            )
            for link in resident.unit_links
        ],
    )


@router.get("/residents", response_model=ManagementResidentListResponse)
async def list_residents(
    search: str | None = Query(default=None, max_length=100),
    is_active: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    actor: ActorContext = Depends(require_management),
    session: AsyncSession = Depends(get_db_session),
) -> ManagementResidentListResponse:
    items, total = await ManagementService(session).list_residents(
        actor,
        search=search,
        is_active=is_active,
        offset=offset,
        limit=limit,
    )
    return ManagementResidentListResponse(
        items=[_resident_response(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/residents/{resident_id}", response_model=ManagementResidentResponse)
async def get_resident(
    resident_id: UUID,
    actor: ActorContext = Depends(require_management),
    session: AsyncSession = Depends(get_db_session),
) -> ManagementResidentResponse:
    resident = await ManagementService(session).get_resident(str(resident_id), actor)
    return _resident_response(resident)


@router.patch("/residents/{resident_id}", response_model=ManagementResidentResponse)
async def update_resident(
    resident_id: UUID,
    payload: ManagementResidentUpdateRequest,
    actor: ActorContext = Depends(require_management),
    session: AsyncSession = Depends(get_db_session),
) -> ManagementResidentResponse:
    values = payload.model_dump()
    resident = await ManagementService(session).update_resident(
        str(resident_id),
        UpdateResidentCommand(
            changed_fields=frozenset(payload.model_fields_set),
            full_name=payload.full_name,
            email=str(payload.email) if payload.email else None,
            phone=values["phone"],
            is_active=payload.is_active,
        ),
        actor,
    )
    return _resident_response(resident)


@router.delete("/residents/{resident_id}/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resident_account(
    resident_id: UUID,
    actor: ActorContext = Depends(require_management),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    await ManagementService(session).delete_resident_account(str(resident_id), actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_management_account(
    payload: ManagementAccountCreateRequest,
    actor: ActorContext = Depends(require_management_admin),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AccountResponse:
    account = await AuthService(session, settings).create_management_account(
        ManagementRegistrationCommand(
            email=str(payload.email),
            password=payload.password,
            employee_code=payload.employee_code,
            full_name=payload.full_name,
            phone=payload.phone,
            department=payload.department,
            job_title=payload.job_title,
            management_role=payload.management_role,
            project_code=payload.project_code,
            building=payload.building,
        ),
        actor,
    )
    return AccountResponse.model_validate(account)


@router.get("/accounts", response_model=ManagementAccountListResponse)
async def list_management_accounts(
    account_status: AccountStatus | None = Query(default=None, alias="status"),
    management_role: ManagementRole | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    actor: ActorContext = Depends(require_management_admin),
    session: AsyncSession = Depends(get_db_session),
) -> ManagementAccountListResponse:
    items, total = await ManagementService(session).list_accounts(
        actor,
        status=account_status,
        management_role=management_role,
        offset=offset,
        limit=limit,
    )
    return ManagementAccountListResponse(
        items=[AccountResponse.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.patch("/accounts/{account_id}", response_model=AccountResponse)
async def update_management_account(
    account_id: UUID,
    payload: ManagementAccountUpdateRequest,
    actor: ActorContext = Depends(require_management_admin),
    session: AsyncSession = Depends(get_db_session),
) -> AccountResponse:
    values = payload.model_dump()
    account = await ManagementService(session).update_account(
        str(account_id),
        UpdateManagementAccountCommand(
            changed_fields=frozenset(payload.model_fields_set),
            email=str(payload.email) if payload.email else None,
            status=payload.status,
            full_name=payload.full_name,
            phone=values["phone"],
            department=values["department"],
            job_title=values["job_title"],
            management_role=payload.management_role,
            project_code=values["project_code"],
            building=values["building"],
        ),
        actor,
    )
    return AccountResponse.model_validate(account)


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: UUID,
    actor: ActorContext = Depends(require_management),
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    await ManagementService(session).delete_account(str(account_id), actor)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/dashboard", response_model=ManagementDashboardResponse)
async def get_management_dashboard(
    actor: ActorContext = Depends(require_management),
    session: AsyncSession = Depends(get_db_session),
) -> ManagementDashboardResponse:
    data = await ManagementService(session).dashboard(actor)
    return ManagementDashboardResponse.model_validate(data)


@router.patch("/tickets/{ticket_id}/assignment", response_model=TicketResponse)
async def assign_ticket(
    ticket_id: UUID,
    payload: TicketAssignmentRequest,
    actor: ActorContext = Depends(require_management),
    session: AsyncSession = Depends(get_db_session),
) -> TicketResponse:
    ticket = await TicketService(session).assign(
        str(ticket_id),
        str(payload.assignee_account_id) if payload.assignee_account_id else None,
        payload.due_at,
        actor,
    )
    return TicketResponse.model_validate(ticket)
