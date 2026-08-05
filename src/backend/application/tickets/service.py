from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.application.tickets.contracts import CreateTicketCommand
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    InvalidTransitionError,
    NotFoundError,
    ValidationError,
)
from src.backend.domain.identity.enums import AccountStatus, ActorRole, ManagementRole
from src.backend.domain.tickets.enums import TicketPriority, TicketStatus
from src.backend.infrastructure.db.models import Ticket, TicketEvent
from src.backend.infrastructure.db.repositories import AccountRepository, ResidentRepository, TicketRepository

ALLOWED_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.SUBMITTED: {TicketStatus.APPROVED, TicketStatus.REJECTED, TicketStatus.CANCELLED},
    TicketStatus.APPROVED: {TicketStatus.IN_PROGRESS, TicketStatus.CANCELLED},
    TicketStatus.IN_PROGRESS: {TicketStatus.RESOLVED, TicketStatus.CANCELLED},
    TicketStatus.RESOLVED: set(),
    TicketStatus.REJECTED: set(),
    TicketStatus.CANCELLED: set(),
}


class TicketService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tickets = TicketRepository(session)
        self.residents = ResidentRepository(session)
        self.accounts = AccountRepository(session)

    async def create(self, command: CreateTicketCommand, actor: ActorContext) -> Ticket:
        if actor.role is ActorRole.RESIDENT and actor.resident_id != command.resident_id:
            raise AuthorizationError("A resident can only create tickets for their own account")
        if not actor.is_authenticated:
            raise AuthenticationError("Resident authentication is required to create a ticket")

        resident = await self.residents.get(command.resident_id)
        if resident is None or not resident.is_active:
            raise NotFoundError("Resident was not found or is inactive")
        if not await self.residents.has_active_unit(command.resident_id, command.unit_id):
            raise AuthorizationError("Resident does not have access to the selected unit")

        if command.idempotency_key:
            existing = await self.tickets.get_by_idempotency_key(command.resident_id, command.idempotency_key)
            if existing:
                self._assert_same_request(existing, command)
                return existing

        ticket = Ticket(
            ticket_code=self._new_ticket_code(),
            resident_id=command.resident_id,
            unit_id=command.unit_id,
            conversation_id=command.conversation_id,
            source=command.source.value,
            status=TicketStatus.SUBMITTED.value,
            category=command.category,
            priority=command.priority.value,
            title=command.title,
            description=command.description,
            location=command.location,
            idempotency_key=command.idempotency_key,
        )
        ticket.events.append(
            TicketEvent(
                event_type="ticket_submitted",
                actor_type=actor.role.value,
                actor_id=actor.actor_id or actor.resident_id,
                to_status=TicketStatus.SUBMITTED.value,
                payload={"source": command.source.value},
            )
        )
        await self.tickets.add(ticket)
        await self.session.commit()
        created = await self.tickets.get(ticket.id)
        if created is None:
            raise NotFoundError("Created ticket could not be reloaded")
        return created

    async def get(self, ticket_id: str, actor: ActorContext) -> Ticket:
        ticket = await self.tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Ticket was not found")
        self._authorize_read(ticket, actor)
        return ticket

    async def list(
        self,
        actor: ActorContext,
        *,
        status: TicketStatus | None = None,
        source: str | None = None,
        priority: TicketPriority | None = None,
        assigned_to_id: str | None = None,
        resident_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Ticket], int]:
        if not actor.is_authenticated:
            raise AuthenticationError("Authentication is required to list tickets")
        if actor.role is ActorRole.RESIDENT:
            resident_id = actor.resident_id
        elif not actor.is_management:
            raise AuthorizationError("This actor cannot list tickets")

        return await self.tickets.list(
            resident_id=resident_id,
            status=status.value if status else None,
            source=source,
            priority=priority.value if priority else None,
            assigned_to_id=assigned_to_id,
            offset=offset,
            limit=limit,
        )

    async def transition(
        self,
        ticket_id: str,
        target: TicketStatus,
        actor: ActorContext,
        comment: str | None = None,
    ) -> Ticket:
        ticket = await self.tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Ticket was not found")

        current = TicketStatus(ticket.status)
        if current is target:
            self._authorize_read(ticket, actor)
            return ticket
        if target not in ALLOWED_TRANSITIONS[current]:
            raise InvalidTransitionError(f"Ticket cannot move from {current.value} to {target.value}")

        resident_cancelling_own_ticket = (
            actor.role is ActorRole.RESIDENT
            and actor.resident_id == ticket.resident_id
            and target is TicketStatus.CANCELLED
            and current is TicketStatus.SUBMITTED
        )
        if not actor.is_management and not resident_cancelling_own_ticket:
            raise AuthorizationError("Management permission is required for this status transition")

        now = datetime.now(UTC)
        ticket.status = target.value
        if target is TicketStatus.APPROVED:
            ticket.approved_at = now
        if target is TicketStatus.RESOLVED:
            ticket.resolved_at = now
        ticket.events.append(
            TicketEvent(
                event_type="status_changed",
                actor_type=actor.role.value,
                actor_id=actor.actor_id or actor.resident_id,
                from_status=current.value,
                to_status=target.value,
                comment=comment,
            )
        )
        await self.session.commit()
        updated = await self.tickets.get(ticket.id)
        if updated is None:
            raise NotFoundError("Updated ticket could not be reloaded")
        return updated

    async def assign(
        self,
        ticket_id: str,
        assignee_account_id: str | None,
        due_at: datetime | None,
        actor: ActorContext,
    ) -> Ticket:
        if not actor.is_management:
            raise AuthorizationError("Management permission is required to assign tickets")
        ticket = await self.tickets.get(ticket_id)
        if ticket is None:
            raise NotFoundError("Ticket was not found")

        now = datetime.now(UTC)
        if assignee_account_id is None:
            due_at = None
        if due_at is not None:
            normalized_due_at = due_at.replace(tzinfo=UTC) if due_at.tzinfo is None else due_at.astimezone(UTC)
            if normalized_due_at <= now:
                raise ValidationError("Ticket due date must be in the future")
            due_at = normalized_due_at

        if actor.management_role is ManagementRole.STAFF:
            if assignee_account_id != actor.actor_id:
                raise AuthorizationError("Staff can only assign a ticket to themselves")
            if ticket.assigned_to_id not in {None, actor.actor_id}:
                raise AuthorizationError("Ticket is already assigned to another staff member")

        if assignee_account_id:
            assignee = await self.accounts.get(assignee_account_id)
            if (
                assignee is None
                or assignee.role != ActorRole.MANAGEMENT.value
                or assignee.status != AccountStatus.ACTIVE.value
            ):
                raise NotFoundError("Active management assignee was not found")

        previous_assignee = ticket.assigned_to_id
        ticket.assigned_to_id = assignee_account_id
        ticket.assigned_at = now if assignee_account_id else None
        ticket.due_at = due_at
        ticket.events.append(
            TicketEvent(
                event_type="ticket_assigned" if assignee_account_id else "ticket_unassigned",
                actor_type=actor.role.value,
                actor_id=actor.actor_id,
                payload={
                    "previous_assignee_id": previous_assignee,
                    "assignee_account_id": assignee_account_id,
                    "due_at": due_at.isoformat() if due_at else None,
                },
            )
        )
        await self.session.commit()
        updated = await self.tickets.get(ticket.id)
        if updated is None:
            raise NotFoundError("Assigned ticket could not be reloaded")
        return updated

    @staticmethod
    def _authorize_read(ticket: Ticket, actor: ActorContext) -> None:
        if actor.is_management:
            return
        if actor.role is ActorRole.RESIDENT and actor.resident_id == ticket.resident_id:
            return
        if not actor.is_authenticated:
            raise AuthenticationError("Authentication is required to access this ticket")
        raise AuthorizationError("Actor cannot access this ticket")

    @staticmethod
    def _new_ticket_code() -> str:
        date_part = datetime.now(UTC).strftime("%Y%m%d")
        return f"TKT-{date_part}-{uuid4().hex[:8].upper()}"

    @staticmethod
    def _assert_same_request(existing: Ticket, command: CreateTicketCommand) -> None:
        request_values = (
            command.unit_id,
            command.category,
            command.priority.value,
            command.title,
            command.description,
            command.location,
            command.source.value,
        )
        existing_values = (
            existing.unit_id,
            existing.category,
            existing.priority,
            existing.title,
            existing.description,
            existing.location,
            existing.source,
        )
        if request_values != existing_values:
            raise ConflictError("Idempotency key was already used with a different ticket payload")
