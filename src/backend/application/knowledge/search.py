from __future__ import annotations

import re
from collections.abc import Iterable

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.infrastructure.db.models import KnowledgeChunk, KnowledgeDocument


class KnowledgeSearchService:
    """Small lexical adapter over indexed handbook chunks.

    The production vector index can replace this adapter later without changing
    the agent/backend contract. Only chunks belonging to indexed documents are
    exposed to the assistant.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(
        self,
        query: str,
        *,
        project_code: str | None = None,
        building: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        tokens = _tokens(query)
        if not tokens:
            return []

        scope_filters = [KnowledgeDocument.status == "indexed"]
        if project_code:
            scope_filters.append(
                or_(KnowledgeDocument.project_code.is_(None), KnowledgeDocument.project_code == project_code)
            )
        if building:
            scope_filters.append(or_(KnowledgeDocument.building.is_(None), KnowledgeDocument.building == building))
        text_filters = [
            column.ilike(f"%{token}%")
            for token in tokens
            for column in (KnowledgeChunk.content, KnowledgeChunk.section, KnowledgeDocument.title)
        ]
        statement = (
            select(KnowledgeChunk, KnowledgeDocument)
            .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
            .where(*scope_filters, or_(*text_filters))
            .limit(max(limit * 8, 20))
        )
        rows = list((await self.session.execute(statement)).all())
        ranked = sorted(rows, key=lambda row: _score(row[0], row[1], tokens), reverse=True)[:limit]
        return [_result(chunk, document) for chunk, document in ranked]


def _tokens(value: str) -> list[str]:
    return list(dict.fromkeys(token for token in re.findall(r"[\wÀ-ỹ]{2,}", value.casefold()) if token))


def _score(chunk: KnowledgeChunk, document: KnowledgeDocument, tokens: Iterable[str]) -> int:
    haystack = " ".join((document.title, chunk.section or "", chunk.content)).casefold()
    return sum(haystack.count(token) for token in tokens)


def _result(chunk: KnowledgeChunk, document: KnowledgeDocument) -> dict:
    return {
        "content": chunk.content,
        "citation": {
            "title": document.title,
            "section": chunk.section,
            "page": chunk.page_number,
            "source_id": document.id,
        },
    }
