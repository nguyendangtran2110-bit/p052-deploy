from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.application.management.contracts import UpdateManagementAccountCommand
from src.backend.domain.common.auth import ActorContext
from src.backend.domain.common.errors import AuthorizationError, ConflictError, NotFoundError
from src.backend.domain.identity.enums import AccountStatus, ActorRole, ManagementRole
from src.backend.domain.tickets.enums import TicketPriority, TicketStatus
from src.backend.infrastructure.db.models import KnowledgeDocument, Resident, Ticket, Unit, UserAccount
from src.backend.infrastructure.db.repositories import AccountRepository, RefreshSessionRepository


class ManagementService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.accounts = AccountRepository(session)
        self.refresh_sessions = RefreshSessionRepository(session)

    async def list_accounts(
        self,
        actor: ActorContext,
        *,
        status: AccountStatus | None,
        management_role: ManagementRole | None,
        offset: int,
        limit: int,
    ) -> tuple[list[UserAccount], int]:
        self._require_admin(actor)
        return await self.accounts.list_management(
            status=status,
            management_role=management_role,
            offset=offset,
            limit=limit,
        )

    async def update_account(
        self,
        account_id: str,
        command: UpdateManagementAccountCommand,
        actor: ActorContext,
    ) -> UserAccount:
        self._require_admin(actor)
        account = await self.accounts.get(account_id)
        if account is None or account.role != ActorRole.MANAGEMENT.value or account.management_profile is None:
            raise NotFoundError("Management account was not found")

        profile = account.management_profile
        disabling = "status" in command.changed_fields and command.status is AccountStatus.DISABLED
        demoting_admin = (
            "management_role" in command.changed_fields
            and profile.management_role == ManagementRole.ADMIN.value
            and command.management_role is not ManagementRole.ADMIN
        )
        if account.id == actor.actor_id and (disabling or demoting_admin):
            raise ConflictError("An administrator cannot disable or demote their own account")
        if (disabling or demoting_admin) and profile.management_role == ManagementRole.ADMIN.value:
            if await self.accounts.count_active_admins() <= 1:
                raise ConflictError("At least one active management administrator is required")

        if "email" in command.changed_fields and command.email:
            normalized_email = command.email.strip().lower()
            existing = await self.accounts.get_by_email(normalized_email)
            if existing and existing.id != account.id:
                raise ConflictError("An account already exists for this email")
            account.email = normalized_email
        if "status" in command.changed_fields and command.status:
            account.status = command.status.value
            if command.status is AccountStatus.DISABLED:
                now = datetime.now(UTC)
                account.token_version += 1
                await self.refresh_sessions.revoke_all(account.id, now)
        if "full_name" in command.changed_fields and command.full_name:
            profile.full_name = command.full_name.strip()
        if "management_role" in command.changed_fields and command.management_role:
            profile.management_role = command.management_role.value
            account.token_version += 1
            await self.refresh_sessions.revoke_all(account.id, datetime.now(UTC))

        for field_name in ("phone", "department", "job_title", "project_code", "building"):
            if field_name in command.changed_fields:
                setattr(profile, field_name, getattr(command, field_name))

        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("Management profile conflicts with existing data") from exc
        updated = await self.accounts.get(account.id)
        if updated is None:
            raise NotFoundError("Updated management account could not be reloaded")
        return updated

    async def dashboard(self, actor: ActorContext) -> dict:
        if not actor.is_management:
            raise AuthorizationError("Management permission is required")

        ticket_total = int((await self.session.scalar(select(func.count(Ticket.id)))) or 0)
        status_rows = await self.session.execute(select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status))
        priority_rows = await self.session.execute(
            select(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority)
        )
        terminal_statuses = [TicketStatus.RESOLVED.value, TicketStatus.REJECTED.value, TicketStatus.CANCELLED.value]
        now = datetime.now(UTC)
        unassigned = int(
            (
                await self.session.scalar(
                    select(func.count(Ticket.id)).where(
                        Ticket.assigned_to_id.is_(None), Ticket.status.not_in(terminal_statuses)
                    )
                )
            )
            or 0
        )
        overdue = int(
            (
                await self.session.scalar(
                    select(func.count(Ticket.id)).where(Ticket.due_at < now, Ticket.status.not_in(terminal_statuses))
                )
            )
            or 0
        )
        active_residents = int(
            (await self.session.scalar(select(func.count(Resident.id)).where(Resident.is_active.is_(True)))) or 0
        )
        active_units = int(
            (await self.session.scalar(select(func.count(Unit.id)).where(Unit.is_active.is_(True)))) or 0
        )
        active_management = int(
            (
                await self.session.scalar(
                    select(func.count(UserAccount.id)).where(
                        UserAccount.role == ActorRole.MANAGEMENT.value,
                        UserAccount.status == AccountStatus.ACTIVE.value,
                    )
                )
            )
            or 0
        )
        pending_knowledge = int(
            (
                await self.session.scalar(
                    select(func.count(KnowledgeDocument.id)).where(
                        KnowledgeDocument.status.in_(["pending", "indexing", "failed"])
                    )
                )
            )
            or 0
        )

        status_counts = {status.value: 0 for status in TicketStatus}
        status_counts.update({str(key): int(value) for key, value in status_rows})
        priority_counts = {priority.value: 0 for priority in TicketPriority}
        priority_counts.update({str(key): int(value) for key, value in priority_rows})
        return {
            "ticket_total": ticket_total,
            "ticket_status_counts": status_counts,
            "ticket_priority_counts": priority_counts,
            "unassigned_tickets": unassigned,
            "overdue_tickets": overdue,
            "active_residents": active_residents,
            "active_units": active_units,
            "active_management_accounts": active_management,
            "knowledge_documents_requiring_attention": pending_knowledge,
        }

    @staticmethod
    def _require_admin(actor: ActorContext) -> None:
        if not actor.is_management_admin:
            raise AuthorizationError("Management administrator permission is required")
