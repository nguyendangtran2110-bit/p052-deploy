from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.api.dependencies import require_management, require_resident
from src.backend.application.onboarding.service import OnboardingService
from src.backend.domain.common.auth import ActorContext
from src.backend.infrastructure.db.session import get_db_session
from src.backend.schemas.onboarding import (
    ManagementOnboardingChecklistResponse,
    ManagementOnboardingListResponse,
    OnboardingChecklistResponse,
    OnboardingItemResponse,
    OnboardingItemStatusRequest,
    OnboardingListResponse,
    OnboardingUnitResponse,
)

resident_router = APIRouter(prefix="/onboarding", tags=["onboarding"])
management_router = APIRouter(prefix="/management/onboarding", tags=["management-onboarding"])


def _item_response(item) -> OnboardingItemResponse:
    return OnboardingItemResponse(
        id=item.id,
        code=item.code,
        category=item.category,
        item_type=item.item_type,
        title=item.title,
        summary=item.summary,
        handbook_reference=item.handbook_reference,
        is_required=item.is_required,
        sort_order=item.sort_order,
        status=item.status,
        acted_at=item.acted_at,
        updated_at=item.updated_at,
    )


def _checklist_response(checklist, *, include_resident: bool = False):
    progress = OnboardingService.progress(checklist)
    response = OnboardingChecklistResponse(
        id=checklist.id,
        resident_id=checklist.resident_id,
        unit_id=checklist.unit_id,
        unit=OnboardingUnitResponse(
            id=checklist.unit.id,
            project_code=checklist.unit.project_code,
            building=checklist.unit.building,
            floor=checklist.unit.floor,
            unit_number=checklist.unit.unit_number,
        ),
        **progress,
        completed_at=checklist.completed_at,
        updated_at=checklist.updated_at,
        items=[_item_response(item) for item in checklist.items],
    )
    if include_resident:
        return ManagementOnboardingChecklistResponse(
            **response.model_dump(),
            resident_code=checklist.resident.resident_code,
            resident_name=checklist.resident.full_name,
        )
    return response


@resident_router.get("", response_model=OnboardingListResponse)
async def get_my_onboarding(
    unit_id: UUID | None = Query(default=None),
    actor: ActorContext = Depends(require_resident),
    session: AsyncSession = Depends(get_db_session),
) -> OnboardingListResponse:
    checklists = await OnboardingService(session).list_for_resident(actor, str(unit_id) if unit_id else None)
    return OnboardingListResponse(items=[_checklist_response(checklist) for checklist in checklists])


@resident_router.patch("/items/{item_id}", response_model=OnboardingItemResponse)
async def update_my_onboarding_item(
    item_id: UUID,
    request: OnboardingItemStatusRequest,
    actor: ActorContext = Depends(require_resident),
    session: AsyncSession = Depends(get_db_session),
) -> OnboardingItemResponse:
    item = await OnboardingService(session).update_item(str(item_id), request.status, actor)
    return _item_response(item)


@management_router.get("", response_model=ManagementOnboardingListResponse)
async def list_onboarding_progress(
    search: str | None = Query(default=None, max_length=100),
    project_code: str | None = Query(default=None, max_length=50),
    building: str | None = Query(default=None, max_length=100),
    is_completed: bool | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    actor: ActorContext = Depends(require_management),
    session: AsyncSession = Depends(get_db_session),
) -> ManagementOnboardingListResponse:
    checklists, total = await OnboardingService(session).list_management(
        actor,
        search=search,
        project_code=project_code,
        building=building,
        is_completed=is_completed,
        offset=offset,
        limit=limit,
    )
    return ManagementOnboardingListResponse(
        items=[_checklist_response(checklist, include_resident=True) for checklist in checklists],
        total=total,
        offset=offset,
        limit=limit,
    )


@management_router.get("/{resident_id}", response_model=ManagementOnboardingListResponse)
async def get_resident_onboarding_progress(
    resident_id: UUID,
    actor: ActorContext = Depends(require_management),
    session: AsyncSession = Depends(get_db_session),
) -> ManagementOnboardingListResponse:
    checklists = await OnboardingService(session).get_management_resident(str(resident_id), actor)
    return ManagementOnboardingListResponse(
        items=[_checklist_response(checklist, include_resident=True) for checklist in checklists],
        total=len(checklists),
        offset=0,
        limit=len(checklists),
    )
