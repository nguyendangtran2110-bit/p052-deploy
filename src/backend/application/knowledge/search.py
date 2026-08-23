from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.backend.core.config import get_settings
from src.backend.infrastructure.db.models import KnowledgeChunk, KnowledgeDocument

_MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
_BOLD_HEADING_RE = re.compile(r"^\s*\*\*(.+?)\*\*\s*$")
_NUMBERED_HEADING_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+\S")
_TOKEN_RE = re.compile(r"[a-z0-9]+")

_STOP_WORDS = frozenset(
    {
        "a",
        "anh",
        "bao",
        "ban",
        "co",
        "cua",
        "cac",
        "cho",
        "den",
        "duoc",
        "em",
        "gi",
        "giup",
        "hay",
        "hoi",
        "khi",
        "la",
        "lam",
        "mot",
        "nao",
        "nay",
        "nhu",
        "nhung",
        "o",
        "se",
        "sao",
        "tai",
        "the",
        "theo",
        "thi",
        "toi",
        "trong",
        "tu",
        "ve",
        "voi",
        "xin",
        "y",
    }
)

_QUERY_ALIASES = {
    "pet": ("vat nuoi",),
    "pets": ("vat nuoi",),
    "thu cung": ("vat nuoi",),
    "cho meo": ("vat nuoi",),
    "ho boi": ("tien ich", "be canh quan"),
    "be boi": ("tien ich", "be canh quan"),
    "sua nha": ("thi cong", "cai tao"),
    "bao tri": ("bao duong", "sua chua"),
    "ban quan ly": ("don vi quan ly van hanh",),
}


@dataclass(frozen=True)
class _LocalChunk:
    content: str
    normalized_content: str
    tokens: tuple[str, ...]
    section: str
    start_line: int
    end_line: int


class KnowledgeSearchService:
    """Hybrid adapter for indexed handbook chunks and a local markdown mock.

    The local path is intentionally small and deterministic: it chunks the
    markdown file, ranks matching chunks lexically, and sends only the best
    chunks to the agent. A vector index can replace this adapter later.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        settings = get_settings()
        configured_file = settings.handbook_context_file.strip()
        self.context_file = Path(configured_file) if configured_file else None
        self.chunk_max_chars = settings.handbook_chunk_max_chars
        self.context_top_k = settings.handbook_context_top_k
        self.context_min_score = settings.handbook_context_min_score

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

        # 1. Primary: Vector search from ChromaDB knowledge base
        vector_results = self._search_vector(query, limit=limit, building=building or project_code)
        if vector_results:
            return vector_results

        # 2. Secondary fallback: Local markdown file search (if configured)
        local_results = self._search_local(query, min(limit, self.context_top_k))
        if local_results:
            return local_results

        # 3. Database SQL fallback: Indexed KnowledgeDocument/KnowledgeChunk tables
        if self.session is None:
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

    def _search_vector(
        self,
        query: str,
        limit: int = 5,
        building: str | None = None,
    ) -> list[dict]:
        try:
            from src.services.rag import retrieve_context

            chunks = retrieve_context(query, top_k=limit, building_id=building)
            if not chunks and building:
                # If building-filtered search returned nothing, retry without building filter
                chunks = retrieve_context(query, top_k=limit, building_id=None)

            if not chunks:
                return []

            return [
                {
                    "content": chunk.text,
                    "citation": {
                        "title": chunk.source_file or "Resident Handbook",
                        "section": chunk.section_title or "Resident Handbook",
                        "page": chunk.page_number if chunk.page_number else None,
                        "source_id": chunk.source_file or "handbook",
                        "source_type": "vector_store",
                        "score": round(chunk.score, 4),
                    },
                }
                for chunk in chunks
            ]
        except Exception:
            return []

    def _search_local(self, query: str, limit: int) -> list[dict]:
        if self.context_file is None or limit <= 0:
            return []
        try:
            path = self.context_file.resolve()
            stat = path.stat()
        except OSError:
            return []
        if not path.is_file() or stat.st_size == 0:
            return []

        chunks = _load_chunks(path, stat.st_mtime_ns, self.chunk_max_chars)
        if not chunks:
            return []
        terms, phrases = _query_terms(query)
        if not terms:
            return []

        document_frequency = Counter(
            term for chunk in chunks for term in set(chunk.tokens) if term in terms
        )
        scored = []
        for chunk in chunks:
            score = _local_score(chunk, terms, phrases, document_frequency, len(chunks))
            if score >= self.context_min_score:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1].start_line))
        return [_local_result(path, score, chunk) for score, chunk in scored[:limit]]


def _query_terms(query: str) -> tuple[set[str], tuple[str, ...]]:
    normalized_query = _normalize(query)
    phrases = [normalized_query]
    terms = set(_tokens(normalized_query))
    for source, aliases in _QUERY_ALIASES.items():
        if source in normalized_query:
            phrases.extend(aliases)
            for alias in aliases:
                terms.update(_tokens(alias))
    return terms, tuple(phrase for phrase in phrases if len(phrase.split()) > 1)


def _local_score(
    chunk: _LocalChunk,
    terms: set[str],
    phrases: tuple[str, ...],
    document_frequency: Counter,
    document_count: int,
) -> float:
    counts = Counter(chunk.tokens)
    score = 0.0
    for term in terms:
        frequency = counts.get(term, 0)
        if not frequency:
            continue
        inverse_frequency = math.log((document_count + 1) / (document_frequency.get(term, 0) + 1)) + 1
        score += inverse_frequency * min(frequency, 3)

    for phrase in phrases:
        if phrase and phrase in chunk.normalized_content:
            score += 5.0

    section_tokens = set(_tokens(chunk.section))
    score += 2.0 * len(section_tokens.intersection(terms))
    return score


def _load_chunks(path: Path, modified_ns: int, max_chars: int) -> tuple[_LocalChunk, ...]:
    content = _read_text(path, modified_ns)
    if not content:
        return ()

    chunks: list[_LocalChunk] = []
    heading_path: list[str] = []
    current_lines: list[str] = []
    current_start = 1
    current_length = 0
    in_table_of_contents = False

    def flush(end_line: int) -> None:
        nonlocal current_lines, current_start, current_length
        raw_content = "\n".join(current_lines).strip()
        if raw_content:
            section = " > ".join(heading_path[-3:])
            prefix = f"Section: {section}\n\n" if section else ""
            full_content = f"{prefix}{raw_content}"
            chunks.append(
                _LocalChunk(
                    content=full_content,
                    normalized_content=_normalize(full_content),
                    tokens=tuple(_tokens(full_content)),
                    section=section,
                    start_line=current_start,
                    end_line=end_line,
                )
            )
        current_lines = []
        current_length = 0

    for line_number, line in enumerate(content.splitlines(), start=1):
        normalized_line = _normalize(line).strip()
        if normalized_line == "muc luc":
            in_table_of_contents = True
            continue
        if in_table_of_contents:
            if normalized_line.startswith("loi noi dau"):
                in_table_of_contents = False
            else:
                continue

        heading = _extract_heading(line)
        if heading:
            normalized_heading = _normalize(heading)
            if normalized_heading.startswith("phan ") or normalized_heading == "loi noi dau":
                heading_path = [heading]
            else:
                heading_path = [*heading_path[-2:], heading]

        if not current_lines:
            current_start = line_number
        line_length = len(line) + 1
        if current_lines and current_length + line_length > max_chars:
            flush(line_number - 1)
            current_start = line_number
        current_lines.append(line)
        current_length += line_length

    if current_lines:
        flush(len(content.splitlines()))
    return tuple(chunks)


def _extract_heading(line: str) -> str | None:
    stripped = line.strip()
    markdown_match = _MARKDOWN_HEADING_RE.match(stripped)
    if markdown_match:
        return markdown_match.group(1).strip()
    bold_match = _BOLD_HEADING_RE.match(stripped)
    candidate = bold_match.group(1).strip() if bold_match else stripped
    candidate = candidate.strip("*_ ")
    normalized = _normalize(candidate)
    if (
        _NUMBERED_HEADING_RE.match(normalized)
        or normalized.startswith("phan ")
        or normalized in {"loi noi dau", "muc luc"}
        or (candidate.isupper() and len(candidate) <= 140)
    ):
        return candidate
    return None


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _tokens(value: str) -> list[str]:
    normalized = _normalize(value)
    return list(
        dict.fromkeys(
            token
            for token in _TOKEN_RE.findall(normalized)
            if len(token) >= 2 and token not in _STOP_WORDS
        )
    )


@lru_cache(maxsize=16)
def _read_text(path: Path, modified_ns: int) -> str:
    """Cache the file between messages and invalidate it when it changes."""
    del modified_ns
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return ""


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


def _local_result(path: Path, score: float, chunk: _LocalChunk) -> dict:
    return {
        "content": chunk.content,
        "citation": {
            "title": path.name,
            "section": chunk.section or "Local handbook context",
            "page": None,
            "line_start": chunk.start_line,
            "line_end": chunk.end_line,
            "source_id": path.name,
            "source_type": "local_file",
            "score": round(score, 3),
        },
    }
