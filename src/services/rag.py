"""
RAG retrieval service for the Resident Handbook.

This module is the ONLY place in the codebase that knows about ChromaDB and
LlamaIndex. All other layers (agent tools, API routes) call retrieve_context()
or query_handbook().

Usage:
    from src.services.rag import retrieve_context, query_handbook
    chunks = retrieve_context("What are the quiet hours?")
    answer = query_handbook("What are the quiet hours?")
"""

from functools import lru_cache
from pathlib import Path
import re
import unicodedata

import llama_index.llms.openai.utils as openai_utils
import tiktoken.model as tiktoken_model

# Register Qwen model in LlamaIndex & Tiktoken for OpenAI compatibility
openai_utils.ALL_AVAILABLE_MODELS["qwen3.5-plus"] = 1_000_000
openai_utils.CHAT_MODELS["qwen3.5-plus"] = 1_000_000
tiktoken_model.MODEL_TO_ENCODING["qwen3.5-plus"] = "cl100k_base"

COLLECTION_NAME = "resident_handbook"
PROCESSED_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"


class RetrievedChunk:
    """A single chunk retrieved from the vector store with metadata."""

    def __init__(
        self,
        text: str,
        source_file: str = "",
        page_number: int = 0,
        section_title: str = "",
        score: float = 0.0,
    ):
        self.text = text
        self.source_file = source_file
        self.page_number = page_number
        self.section_title = section_title
        self.score = score

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "source_file": self.source_file,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "score": round(self.score, 4),
        }


def _get_persist_dir() -> str:
    """Read the ChromaDB path from config, falling back to env or default."""
    # Import inside function to avoid circular imports at module load time.
    from src.config import get_settings
    return get_settings().chroma_persist_dir


def get_chroma_client(settings, persist_dir: str):
    """
    Instantiate a ChromaDB client in Dual-Mode:
    - Mode 1 (HttpClient): Active when settings.chroma_server_host is set (Docker / Production).
    - Mode 2 (PersistentClient): Active for local offline development & unit testing.
    """
    import chromadb

    if getattr(settings, "chroma_server_host", ""):
        return chromadb.HttpClient(
            host=settings.chroma_server_host,
            port=getattr(settings, "chroma_server_port", 8000),
            ssl=getattr(settings, "chroma_server_ssl", False),
        )
    return chromadb.PersistentClient(path=persist_dir)


def is_qdrant_enabled(settings) -> bool:
    """Check if Qdrant is selected or auto-detected via QDRANT_URL."""
    store_type = getattr(settings, "vector_store_type", "auto")
    if store_type == "qdrant":
        return True
    if store_type == "auto" and bool(getattr(settings, "qdrant_url", "")):
        return True
    return False


def get_qdrant_client(settings):
    """Instantiate a Qdrant client using configured cloud or local URL."""
    from qdrant_client import QdrantClient

    url = getattr(settings, "qdrant_url", "")
    api_key = getattr(settings, "qdrant_api_key", "") or None
    return QdrantClient(url=url, api_key=api_key)


def ensure_qdrant_payload_index(client, collection_name: str, field_name: str = "building_id") -> None:
    """Ensure keyword payload index exists in Qdrant for filtering."""
    try:
        from qdrant_client.http import models as qmodels

        client.create_payload_index(
            collection_name=collection_name,
            field_name=field_name,
            field_schema=qmodels.PayloadSchemaType.KEYWORD,
        )
    except Exception:
        pass


@lru_cache(maxsize=1)
def _get_vector_index_cached(
    persist_dir: str,
    api_key: str,
    base_url: str,
    chroma_host: str,
    model_name: str,
    store_type: str = "auto",
    qdrant_url: str = "",
    qdrant_api_key: str = "",
    qdrant_collection: str = "",
):
    """
    Build and cache the LlamaIndex VectorStoreIndex.
    Supports both Qdrant (Cloud / Local) and ChromaDB.
    """
    from llama_index.core import VectorStoreIndex
    from llama_index.embeddings.openai import OpenAIEmbedding

    from src.config import get_settings
    settings = get_settings()

    embed_model = OpenAIEmbedding(
        model_name=model_name,
        api_key=api_key,
        api_base=base_url,
        embed_batch_size=10,
        timeout=8.0,
        max_retries=1,
    )

    if is_qdrant_enabled(settings):
        from llama_index.vector_stores.qdrant import QdrantVectorStore
        from qdrant_client import QdrantClient

        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key or None)
        collection = qdrant_collection or getattr(settings, "qdrant_collection_name", COLLECTION_NAME) or COLLECTION_NAME
        ensure_qdrant_payload_index(client, collection, field_name="building_id")
        vector_store = QdrantVectorStore(client=client, collection_name=collection)
        return VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

    from llama_index.vector_stores.chroma import ChromaVectorStore

    db = get_chroma_client(settings, persist_dir)
    chroma_collection = db.get_or_create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    return VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)


def _get_vector_index(persist_dir: str):
    from src.config import get_settings
    settings = get_settings()
    api_key = settings.qwen_api_key or settings.openai_api_key
    base_url = settings.qwen_api_base or settings.openai_api_base
    chroma_host = getattr(settings, "chroma_server_host", "")
    model_name = settings.embedding_model_name
    store_type = getattr(settings, "vector_store_type", "auto")
    qdrant_url = getattr(settings, "qdrant_url", "")
    qdrant_api_key = getattr(settings, "qdrant_api_key", "")
    qdrant_collection = getattr(settings, "qdrant_collection_name", COLLECTION_NAME)
    return _get_vector_index_cached(
        persist_dir,
        api_key,
        base_url,
        chroma_host,
        model_name,
        store_type,
        qdrant_url,
        qdrant_api_key,
        qdrant_collection,
    )


def _collection_count(settings, persist_dir: str) -> int:
    """Return the indexed document count without invoking the embedding API."""
    try:
        if is_qdrant_enabled(settings):
            client = get_qdrant_client(settings)
            collection = getattr(settings, "qdrant_collection_name", COLLECTION_NAME) or COLLECTION_NAME
            info = client.get_collection(collection_name=collection)
            return info.points_count or 0

        db = get_chroma_client(settings, persist_dir)
        return db.get_or_create_collection(COLLECTION_NAME).count()
    except Exception:
        return 0


def _normalize_search_text(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def _retrieve_local_processed_context(
    query: str, top_k: int, building_id: str | None = None
) -> list[RetrievedChunk]:
    """Small offline fallback for processed markdown when vector retrieval is unavailable."""
    query_text = _normalize_search_text(query)
    terms = {term for term in query_text.split() if len(term) > 1}
    if not terms:
        return []

    candidates: list[RetrievedChunk] = []
    for path in sorted(PROCESSED_DATA_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
        for paragraph in paragraphs:
            normalized = _normalize_search_text(paragraph)
            matched = terms.intersection(normalized.split())
            if not matched:
                continue
            score = len(matched) / max(len(terms), 1)
            if "phu dong" in normalized or "sky garden" in normalized:
                score += 0.25
            candidates.append(RetrievedChunk(paragraph, path.name, score=score))

    candidates.sort(key=lambda chunk: chunk.score, reverse=True)
    return candidates[:top_k]


def _build_retriever(persist_dir: str, building_id: str | None = None, top_k: int = 5):
    """
    Build LlamaIndex VectorIndexRetriever with optional multi-tenant MetadataFilter.
    """
    from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters

    index = _get_vector_index(persist_dir)
    filters = None
    if building_id:
        filters = MetadataFilters(filters=[ExactMatchFilter(key="building_id", value=building_id)])

    return index.as_retriever(similarity_top_k=top_k, filters=filters)


def retrieve_context(query: str, top_k: int = 5, building_id: str | None = None) -> list[RetrievedChunk]:
    """
    Retrieve relevant chunks from the handbook vector store.

    Uses Qwen embedding for vector similarity search.
    Returns a list of RetrievedChunk objects with text and metadata.

    Args:
        query: The search query (in any language).
        top_k: Number of top chunks to retrieve.
        building_id: Optional tenant isolation filter (e.g. 'phu_dong_sky_garden').

    Returns:
        List of RetrievedChunk objects sorted by relevance.
    """
    from src.config import get_settings
    settings = get_settings()
    persist_dir = _get_persist_dir()

    if not getattr(settings, "chroma_server_host", "") and not Path(persist_dir).exists():
        return _retrieve_local_processed_context(query, top_k, building_id)

    if _collection_count(settings, persist_dir) == 0:
        return _retrieve_local_processed_context(query, top_k, building_id)

    try:
        retriever = _build_retriever(persist_dir, building_id=building_id, top_k=top_k)
        nodes = retriever.retrieve(query)

        chunks = []
        for node in nodes[:top_k]:
            metadata = node.metadata or {}
            chunk = RetrievedChunk(
                text=node.get_content(),
                source_file=metadata.get("source_file", ""),
                page_number=metadata.get("page_number", 0),
                section_title=metadata.get("section_title", metadata.get("Header 1", "")),
                score=node.score if node.score is not None else 0.0,
            )
            chunks.append(chunk)

        return chunks
    except Exception as exc:
        print(f"[rag] Retrieval error: {type(exc).__name__}: {exc}")
        return _retrieve_local_processed_context(query, top_k, building_id)


def _build_query_engine(persist_dir: str, building_id: str | None = None):
    """
    Build LlamaIndex QueryEngine with optional multi-tenant MetadataFilter.
    """
    from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
    from llama_index.llms.openai import OpenAI as LlamaIndexOpenAI

    from src.config import get_settings
    settings = get_settings()

    api_key = settings.qwen_api_key or settings.openai_api_key
    base_url = settings.qwen_api_base or settings.openai_api_base

    llm = LlamaIndexOpenAI(
        model=settings.model_name,
        api_key=api_key,
        api_base=base_url,
        temperature=settings.llm_temperature,
    )

    index = _get_vector_index(persist_dir)

    filters = None
    if building_id:
        filters = MetadataFilters(filters=[ExactMatchFilter(key="building_id", value=building_id)])

    return index.as_query_engine(
        llm=llm,
        similarity_top_k=3,
        filters=filters,
        response_mode="compact",
    )


def query_handbook(query: str, building_id: str | None = None) -> str:
    """
    Query the resident handbook knowledge base.

    Returns a grounded answer drawn from the indexed handbook sections.
    If building_id is provided, filters retrieval strictly to that building.

    Args:
        query: The question to answer.
        building_id: Optional tenant isolation filter (e.g. 'phu_dong_sky_garden').

    Returns:
        A plain-text answer with source context, or a degradation message.
    """
    from src.config import get_settings
    settings = get_settings()
    persist_dir = _get_persist_dir()

    if not getattr(settings, "chroma_server_host", "") and not Path(persist_dir).exists():
        return (
            "The resident handbook knowledge base is not available yet. "
            "Please ask a management staff member for assistance."
        )

    try:
        engine = _build_query_engine(persist_dir, building_id=building_id)
        response = engine.query(query)
        return str(response)
    except Exception as exc:  # pragma: no cover — surface runtime errors safely
        return (
            f"Could not retrieve an answer from the handbook at this time "
            f"({type(exc).__name__}). Please contact the management office."
        )
