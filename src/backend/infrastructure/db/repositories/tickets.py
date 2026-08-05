from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.infrastructure.db.models import Ticket


class TicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, ticket: Ticket) -> None:
        self.session.add(ticket)
        await self.session.flush()

    async def get(self, ticket_id: str) -> Ticket | None:
        statement = (
            select(Ticket)
            .options(selectinload(Ticket.events), selectinload(Ticket.attachments))
            .where(Ticket.id == ticket_id)
        )
        return await self.session.scalar(statement)

    async def get_by_idempotency_key(self, resident_id: str, key: str) -> Ticket | None:
        statement = (
            select(Ticket)
            .options(selectinload(Ticket.events), selectinload(Ticket.attachments))
            .where(Ticket.resident_id == resident_id, Ticket.idempotency_key == key)
        )
        return await self.session.scalar(statement)

    async def list(
        self,
        *,
        resident_id: str | None = None,
        status: str | None = None,
        source: str | None = None,
        priority: str | None = None,
        assigned_to_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Ticket], int]:
        filters = []
        if resident_id:
            filters.append(Ticket.resident_id == resident_id)
        if status:
            filters.append(Ticket.status == status)
        if source:
            filters.append(Ticket.source == source)
        if priority:
            filters.append(Ticket.priority == priority)
        if assigned_to_id:
            filters.append(Ticket.assigned_to_id == assigned_to_id)

        statement = select(Ticket).where(*filters).order_by(Ticket.created_at.desc()).offset(offset).limit(limit)
        count_statement = select(func.count(Ticket.id)).where(*filters)
        items = list((await self.session.scalars(statement)).all())
        total = int((await self.session.scalar(count_statement)) or 0)
        return items, total
