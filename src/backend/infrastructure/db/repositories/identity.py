from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.domain.identity.enums import AccountStatus, ActorRole, ManagementRole
from src.backend.infrastructure.db.models import ManagementProfile, RefreshSession, UserAccount


class AccountRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, account: UserAccount) -> None:
        self.session.add(account)
        await self.session.flush()

    async def get(self, account_id: str) -> UserAccount | None:
        statement = (
            select(UserAccount)
            .options(selectinload(UserAccount.management_profile))
            .where(UserAccount.id == account_id)
        )
        return await self.session.scalar(statement)

    async def get_by_email(self, email: str) -> UserAccount | None:
        statement = (
            select(UserAccount).options(selectinload(UserAccount.management_profile)).where(UserAccount.email == email)
        )
        return await self.session.scalar(statement)

    async def get_by_resident(self, resident_id: str) -> UserAccount | None:
        statement = select(UserAccount).where(UserAccount.resident_id == resident_id)
        return await self.session.scalar(statement)

    async def count_management(self) -> int:
        statement = select(func.count(UserAccount.id)).where(UserAccount.role == ActorRole.MANAGEMENT.value)
        return int((await self.session.scalar(statement)) or 0)

    async def count_active_admins(self) -> int:
        statement = (
            select(func.count(UserAccount.id))
            .join(ManagementProfile, ManagementProfile.account_id == UserAccount.id)
            .where(
                UserAccount.role == ActorRole.MANAGEMENT.value,
                UserAccount.status == AccountStatus.ACTIVE.value,
                ManagementProfile.management_role == ManagementRole.ADMIN.value,
            )
        )
        return int((await self.session.scalar(statement)) or 0)

    async def list_management(
        self,
        *,
        status: AccountStatus | None = None,
        management_role: ManagementRole | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[UserAccount], int]:
        filters = [UserAccount.role == ActorRole.MANAGEMENT.value]
        if status:
            filters.append(UserAccount.status == status.value)
        if management_role:
            filters.append(ManagementProfile.management_role == management_role.value)

        statement = (
            select(UserAccount)
            .join(ManagementProfile)
            .options(selectinload(UserAccount.management_profile))
            .where(*filters)
            .order_by(UserAccount.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count(UserAccount.id)).join(ManagementProfile).where(*filters)
        items = list((await self.session.scalars(statement)).all())
        total = int((await self.session.scalar(count_statement)) or 0)
        return items, total


class RefreshSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, refresh_session: RefreshSession) -> None:
        self.session.add(refresh_session)
        await self.session.flush()

    async def get(self, session_id: str) -> RefreshSession | None:
        return await self.session.get(RefreshSession, session_id)

    async def get_for_update(self, session_id: str) -> RefreshSession | None:
        statement = select(RefreshSession).where(RefreshSession.id == session_id).with_for_update()
        return await self.session.scalar(statement)

    async def revoke_all(self, account_id: str, revoked_at: datetime) -> None:
        statement = (
            update(RefreshSession)
            .where(RefreshSession.account_id == account_id, RefreshSession.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
        )
        await self.session.execute(statement)
