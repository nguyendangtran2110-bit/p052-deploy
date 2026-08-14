from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import require_management
from src.backend.application.residents.contracts import CreateUnitCommand
from src.backend.application.residents.service import ResidentService
from src.backend.domain.common.auth import ActorContext
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.residents import UnitCreate, UnitResponse

router = APIRouter(prefix="/units", tags=["units"])


@router.post("", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
async def create_unit(
    request: UnitCreate,
    session: AsyncSession = Depends(get_db_session),
    _actor: ActorContext = Depends(require_management),
) -> UnitResponse:
    unit = await ResidentService(session).create_unit(
        CreateUnitCommand(
            project_code=request.project_code,
            building=request.building,
            floor=request.floor,
            unit_number=request.unit_number,
        )
    )
    return UnitResponse.model_validate(unit)


@router.get("", response_model=list[UnitResponse])
async def list_units(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
    _actor: ActorContext = Depends(require_management),
) -> list[UnitResponse]:
    units = await ResidentService(session).list_units(offset, limit)
    return [UnitResponse.model_validate(unit) for unit in units]
