from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infrastructure.db.models import Resident, ResidentUnit, Unit


class ResidentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, resident_id: str) -> Resident | None:
        return await self.session.get(Resident, resident_id)

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
