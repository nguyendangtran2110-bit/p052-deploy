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


@lru_cache(maxsize=1)
def _build_retriever(persist_dir: str):
    """
    Build and cache a LlamaIndex VectorIndexRetriever.

    Uses Qwen embedding (DashScope) for vector search since the data
    was indexed with Qwen embedding. The LLM generation is handled
    separately by Groq.
    """
    import chromadb
    from llama_index.core import VectorStoreIndex
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.vector_stores.chroma import ChromaVectorStore

    from src.config import get_settings
    settings = get_settings()

    api_key = settings.qwen_api_key or settings.openai_api_key
    base_url = settings.qwen_api_base or settings.openai_api_base

    embed_model = OpenAIEmbedding(
        model_name=settings.embedding_model_name,
        api_key=api_key,
        api_base=base_url,
        embed_batch_size=10,
    )

    db = chromadb.PersistentClient(path=persist_dir)
    chroma_collection = db.get_or_create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

    return index.as_retriever(similarity_top_k=5)


def retrieve_context(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    """
    Retrieve relevant chunks from the handbook vector store.

    Uses Qwen embedding for vector similarity search.
    Returns a list of RetrievedChunk objects with text and metadata.

    Args:
        query: The search query (in any language).
        top_k: Number of top chunks to retrieve.

    Returns:
        List of RetrievedChunk objects sorted by relevance.
    """
    persist_dir = _get_persist_dir()

    if not Path(persist_dir).exists():
        return []

    try:
        retriever = _build_retriever(persist_dir)
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


def query_handbook(query: str) -> str:
    """
    Query the resident handbook knowledge base (backward-compatible).

    Returns a grounded answer drawn from the indexed handbook sections.
    If the vector store has not been built yet, returns a safe degradation
    message instead of raising an exception.

    Args:
        query: The question to answer (in any language; model handles translation).

    Returns:
        A plain-text answer with source context, or a degradation message.
    """
    chunks = retrieve_context(query, top_k=3)

    if not chunks:
        return (
            "The resident handbook knowledge base is not available yet. "
            "Please ask a management staff member for assistance."
        )

    # Format chunks into a simple text response
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source_info = f"[{chunk.source_file}"
        if chunk.page_number:
            source_info += f", p.{chunk.page_number}"
        source_info += "]"
        context_parts.append(f"{i}. {source_info} {chunk.text[:200]}...")

    return "\n".join(context_parts)
