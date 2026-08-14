from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import require_management, require_resident
from src.backend.application.residents.contracts import CreateResidentCommand
from src.backend.application.residents.service import ResidentService
from src.backend.domain.common.auth import ActorContext
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.residents import (
    ResidentCreate,
    ResidentProfileResponse,
    ResidentResponse,
    ResidentUnitLinkCreate,
    ResidentUnitLinkResponse,
    ResidentUnitSummary,
    UnitResponse,
)

router = APIRouter(prefix="/residents", tags=["residents"])


@router.post("", response_model=ResidentResponse, status_code=status.HTTP_201_CREATED)
async def create_resident(
    request: ResidentCreate,
    session: AsyncSession = Depends(get_db_session),
    _actor: ActorContext = Depends(require_management),
) -> ResidentResponse:
    resident = await ResidentService(session).create_resident(
        CreateResidentCommand(
            resident_code=request.resident_code,
            full_name=request.full_name,
            email=str(request.email) if request.email else None,
            phone=request.phone,
        )
    )
    return ResidentResponse.model_validate(resident)


@router.get("/me", response_model=ResidentProfileResponse)
async def get_my_profile(
    session: AsyncSession = Depends(get_db_session),
    actor: ActorContext = Depends(require_resident),
) -> ResidentProfileResponse:
    resident = await ResidentService(session).get_profile(str(actor.resident_id))
    return ResidentProfileResponse(
        **ResidentResponse.model_validate(resident).model_dump(),
        units=[
            ResidentUnitSummary(
                **UnitResponse.model_validate(link.unit).model_dump(),
                resident_role=link.role,
                is_primary=link.is_primary,
            )
            for link in resident.unit_links
        ],
    )


@router.post("/{resident_id}/units", response_model=ResidentUnitLinkResponse)
async def link_resident_unit(
    resident_id: UUID,
    request: ResidentUnitLinkCreate,
    session: AsyncSession = Depends(get_db_session),
    _actor: ActorContext = Depends(require_management),
) -> ResidentUnitLinkResponse:
    link = await ResidentService(session).link_unit(
        str(resident_id), str(request.unit_id), request.role, request.is_primary
    )
    return ResidentUnitLinkResponse.model_validate(link, from_attributes=True)
