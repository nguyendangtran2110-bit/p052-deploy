from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.infrastructure.db.models import Resident, ResidentUnit, Unit, UserAccount


class ResidentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, resident_id: str) -> Resident | None:
        return await self.session.get(Resident, resident_id)

    async def get_for_management(self, resident_id: str) -> Resident | None:
        statement = (
            select(Resident)
            .options(
                selectinload(Resident.account).selectinload(UserAccount.management_profile),
                selectinload(Resident.unit_links).selectinload(ResidentUnit.unit),
            )
            .where(Resident.id == resident_id)
        )
        return await self.session.scalar(statement)

    async def list_for_management(
        self,
        *,
        search: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Resident], int]:
        filters = []
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Resident.resident_code.ilike(pattern),
                    Resident.full_name.ilike(pattern),
                    Resident.email.ilike(pattern),
                    Resident.phone.ilike(pattern),
                )
            )
        if is_active is not None:
            filters.append(Resident.is_active.is_(is_active))

        statement = (
            select(Resident)
            .options(
                selectinload(Resident.account).selectinload(UserAccount.management_profile),
                selectinload(Resident.unit_links).selectinload(ResidentUnit.unit),
            )
            .where(*filters)
            .order_by(Resident.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count(Resident.id)).where(*filters)
        items = list((await self.session.scalars(statement)).all())
        total = int((await self.session.scalar(count_statement)) or 0)
        return items, total

    async def has_active_unit(self, resident_id: str, unit_id: str) -> bool:
        statement = (
            select(ResidentUnit.resident_id)
            .join(Resident, Resident.id == ResidentUnit.resident_id)
            .join(Unit, Unit.id == ResidentUnit.unit_id)
            .where(
                ResidentUnit.resident_id == resident_id,
                ResidentUnit.unit_id == unit_id,
                Resident.is_active.is_(True),
                Unit.is_active.is_(True),
            )
        )
        return (await self.session.scalar(statement)) is not None
