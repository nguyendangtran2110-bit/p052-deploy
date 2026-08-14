from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.application.residents.contracts import CreateResidentCommand, CreateUnitCommand
from src.backend.domain.common.errors import ConflictError, NotFoundError
from src.backend.domain.residents.enums import ResidentUnitRole
from src.backend.infrastructure.db.models import Resident, ResidentUnit, Unit


class ResidentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_resident(self, command: CreateResidentCommand) -> Resident:
        filters = [Resident.resident_code == command.resident_code]
        if command.email:
            filters.append(Resident.email == command.email.lower())
        if command.phone:
            filters.append(Resident.phone == command.phone)
        existing = await self.session.scalar(select(Resident).where(or_(*filters)))
        if existing:
            raise ConflictError("Resident code, email or phone is already registered")

        resident = Resident(
            resident_code=command.resident_code,
            full_name=command.full_name,
            email=command.email.lower() if command.email else None,
            phone=command.phone,
        )
        self.session.add(resident)
        await self._commit_or_conflict("Resident code, email or phone is already registered")
        return resident

    async def create_unit(self, command: CreateUnitCommand) -> Unit:
        statement = select(Unit).where(
            Unit.project_code == command.project_code,
            Unit.building == command.building,
            Unit.unit_number == command.unit_number,
        )
        if await self.session.scalar(statement):
            raise ConflictError("Unit is already registered")

        unit = Unit(
            project_code=command.project_code,
            building=command.building,
            floor=command.floor,
            unit_number=command.unit_number,
        )
        self.session.add(unit)
        await self._commit_or_conflict("Unit is already registered")
        return unit

    async def link_unit(
        self,
        resident_id: str,
        unit_id: str,
        role: ResidentUnitRole,
        is_primary: bool,
    ) -> ResidentUnit:
        resident = await self.session.get(Resident, resident_id)
        unit = await self.session.get(Unit, unit_id)
        if resident is None:
            raise NotFoundError("Resident was not found")
        if unit is None:
            raise NotFoundError("Unit was not found")

        existing = await self.session.get(ResidentUnit, (resident_id, unit_id))
        if existing:
            if existing.role != role.value or existing.is_primary != is_primary:
                raise ConflictError("Resident is already linked to this unit with different attributes")
            return existing

        link = ResidentUnit(
            resident_id=resident_id,
            unit_id=unit_id,
            role=role.value,
            is_primary=is_primary,
        )
        self.session.add(link)
        await self._commit_or_conflict("Resident is already linked to this unit")
        return link

    async def get_profile(self, resident_id: str) -> Resident:
        statement = (
            select(Resident)
            .options(selectinload(Resident.unit_links).selectinload(ResidentUnit.unit))
            .where(Resident.id == resident_id)
        )
        resident = await self.session.scalar(statement)
        if resident is None:
            raise NotFoundError("Resident was not found")
        return resident

    async def list_units(self, offset: int, limit: int) -> list[Unit]:
        statement = (
            select(Unit).order_by(Unit.project_code, Unit.building, Unit.unit_number).offset(offset).limit(limit)
        )
        return list((await self.session.scalars(statement)).all())

    async def _commit_or_conflict(self, message: str) -> None:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(message) from exc
