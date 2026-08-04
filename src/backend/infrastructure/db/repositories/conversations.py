from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infrastructure.db.models import Conversation


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, conversation: Conversation) -> None:
        self.session.add(conversation)
        await self.session.flush()

    async def get(self, conversation_id: str) -> Conversation | None:
        return await self.session.get(Conversation, conversation_id)
