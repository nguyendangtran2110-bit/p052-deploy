from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infrastructure.db.models import KnowledgeDocument


class KnowledgeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, document: KnowledgeDocument) -> None:
        self.session.add(document)
        await self.session.flush()

    async def get(self, document_id: str) -> KnowledgeDocument | None:
        return await self.session.get(KnowledgeDocument, document_id)

    async def get_by_checksum(self, checksum: str) -> KnowledgeDocument | None:
        statement = select(KnowledgeDocument).where(KnowledgeDocument.checksum_sha256 == checksum)
        return await self.session.scalar(statement)

    async def list(
        self,
        *,
        status: str | None = None,
        document_type: str | None = None,
        project_code: str | None = None,
        building: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[KnowledgeDocument], int]:
        filters = []
        if status:
            filters.append(KnowledgeDocument.status == status)
        if document_type:
            filters.append(KnowledgeDocument.document_type == document_type)
        if project_code:
            filters.append(KnowledgeDocument.project_code == project_code)
        if building:
            filters.append(KnowledgeDocument.building == building)

        statement = (
            select(KnowledgeDocument)
            .where(*filters)
            .order_by(KnowledgeDocument.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_statement = select(func.count(KnowledgeDocument.id)).where(*filters)
        items = list((await self.session.scalars(statement)).all())
        total = int((await self.session.scalar(count_statement)) or 0)
        return items, total
