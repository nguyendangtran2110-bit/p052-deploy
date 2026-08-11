from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.backend.domain.conversations.enums import ConversationHandoffStatus
from src.backend.infrastructure.db.base import utc_now
from src.backend.infrastructure.db.models import Conversation, Message, Ticket


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, conversation: Conversation) -> None:
        self.session.add(conversation)
        await self.session.flush()

    async def get(self, conversation_id: str) -> Conversation | None:
        statement = (
            select(Conversation)
            .options(
                selectinload(Conversation.messages).selectinload(Message.attachments),
                selectinload(Conversation.ticket).selectinload(Ticket.conversation),
                selectinload(Conversation.ticket).selectinload(Ticket.attachments),
            )
            .where(Conversation.id == conversation_id)
        )
        return await self.session.scalar(statement)

    async def list_messages(self, conversation_id: str, limit: int = 100) -> list[Message]:
        statement = (
            select(Message)
            .options(selectinload(Message.attachments))
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list((await self.session.scalars(statement)).all())
        messages.reverse()
        return messages

    async def assign_for_management_message(
        self,
        conversation_id: str,
        manager_id: str,
        *,
        expected_version: int,
    ) -> bool:
        statement = (
            update(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.status == "active",
                Conversation.conversation_version == expected_version,
                or_(
                    Conversation.assigned_manager_id.is_(None),
                    Conversation.assigned_manager_id == manager_id,
                ),
            )
            .values(
                assigned_manager_id=manager_id,
                conversation_version=Conversation.conversation_version + 1,
                handoff_status=ConversationHandoffStatus.MANAGEMENT_ACTIVE.value,
                last_message_at=utc_now(),
            )
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(statement)
        return result.rowcount == 1

    async def release_assignment(
        self,
        conversation_id: str,
        manager_id: str,
        *,
        expected_version: int | None,
        is_admin: bool,
    ) -> bool:
        conditions = [Conversation.id == conversation_id, Conversation.status == "active"]
        if not is_admin:
            conditions.append(Conversation.assigned_manager_id == manager_id)
        if expected_version is not None:
            conditions.append(Conversation.conversation_version == expected_version)
        statement = (
            update(Conversation)
            .where(*conditions)
            .values(
                assigned_manager_id=None,
                conversation_version=Conversation.conversation_version + 1,
                handoff_status=ConversationHandoffStatus.BOT_ACTIVE.value,
                handoff_requested_at=None,
                last_message_at=utc_now(),
            )
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(statement)
        return result.rowcount == 1

    async def take_over(
        self,
        conversation_id: str,
        manager_id: str,
        *,
        expected_version: int,
    ) -> bool:
        statement = (
            update(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.status == "active",
                Conversation.conversation_version == expected_version,
            )
            .values(
                assigned_manager_id=manager_id,
                conversation_version=Conversation.conversation_version + 1,
                handoff_status=ConversationHandoffStatus.MANAGEMENT_ACTIVE.value,
                last_message_at=utc_now(),
            )
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(statement)
        return result.rowcount == 1

    async def bump_version(self, conversation_id: str) -> bool:
        statement = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(conversation_version=Conversation.conversation_version + 1)
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(statement)
        return result.rowcount == 1

    async def list_handoffs(
        self,
        *,
        handoff_status: str,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Conversation], int]:
        handoff_filter = Conversation.handoff_status == handoff_status
        filters = [handoff_filter, Conversation.resident_id.is_not(None)]
        statement = (
            select(Conversation)
            .options(selectinload(Conversation.ticket))
            .where(*filters)
            .order_by(Conversation.last_message_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count(Conversation.id)).where(*filters)
        items = list((await self.session.scalars(statement)).all())
        total = int((await self.session.scalar(count_statement)) or 0)
        return items, total
