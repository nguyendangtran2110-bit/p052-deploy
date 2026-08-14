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

import llama_index.llms.openai.utils as openai_utils
import tiktoken.model as tiktoken_model

# Register Qwen model in LlamaIndex & Tiktoken for OpenAI compatibility
openai_utils.ALL_AVAILABLE_MODELS["qwen3.5-plus"] = 1_000_000
openai_utils.CHAT_MODELS["qwen3.5-plus"] = 1_000_000
tiktoken_model.MODEL_TO_ENCODING["qwen3.5-plus"] = "cl100k_base"

COLLECTION_NAME = "resident_handbook"


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


@lru_cache(maxsize=1)
def _get_vector_index_cached(persist_dir: str, api_key: str, base_url: str, chroma_host: str, model_name: str):
    """
    Build and cache the LlamaIndex VectorStoreIndex.
    Keyed by persist_dir, credentials, and host endpoints so dynamic setting updates
    or test monkeypatching force a cache refresh rather than returning stale instances.
    """
    from llama_index.core import VectorStoreIndex
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.vector_stores.chroma import ChromaVectorStore

    from src.config import get_settings
    settings = get_settings()

    embed_model = OpenAIEmbedding(
        model_name=model_name,
        api_key=api_key,
        api_base=base_url,
        embed_batch_size=10,
    )

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
    return _get_vector_index_cached(persist_dir, api_key, base_url, chroma_host, model_name)


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
        return []

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
        return []


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
