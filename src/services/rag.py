"""
RAG retrieval service for the Resident Handbook.

This module is the ONLY place in the codebase that knows about ChromaDB and
LlamaIndex. All other layers (agent tools, API routes) call query_handbook().

Usage:
    from src.services.rag import query_handbook
    answer = query_handbook("What are the quiet hours?")
"""

import os
from functools import lru_cache
from pathlib import Path

import llama_index.llms.openai.utils as openai_utils
import tiktoken.model as tiktoken_model

# Register Qwen model in LlamaIndex & Tiktoken for OpenAI compatibility
openai_utils.ALL_AVAILABLE_MODELS["qwen3.6-plus"] = 128000
openai_utils.CHAT_MODELS["qwen3.6-plus"] = 128000
tiktoken_model.MODEL_TO_ENCODING["qwen3.6-plus"] = "cl100k_base"

COLLECTION_NAME = "resident_handbook"


def _get_persist_dir() -> str:
    """Read the ChromaDB path from config, falling back to env or default."""
    # Import inside function to avoid circular imports at module load time.
    from src.config import get_settings
    return get_settings().chroma_persist_dir


@lru_cache(maxsize=1)
def _build_query_engine(persist_dir: str):
    """
    Build and cache the LlamaIndex QueryEngine.

    lru_cache(maxsize=1) means the engine is created once per process,
    which avoids re-opening ChromaDB on every query.
    The cache key is persist_dir, so changing the path in config produces
    a new engine automatically.
    """
    import chromadb
    from llama_index.core import VectorStoreIndex
    from llama_index.embeddings.openai import OpenAIEmbedding
    from llama_index.llms.openai import OpenAI as LlamaIndexOpenAI
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
    llm = LlamaIndexOpenAI(
        model=settings.model_name,
        api_key=api_key,
        api_base=base_url,
        temperature=settings.llm_temperature,
    )

    db = chromadb.PersistentClient(path=persist_dir)
    chroma_collection = db.get_or_create_collection(COLLECTION_NAME)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)

    return index.as_query_engine(
        llm=llm,
        similarity_top_k=3,
        # Return source nodes so callers can surface citations.
        response_mode="compact",
    )


def query_handbook(query: str) -> str:
    """
    Query the resident handbook knowledge base.

    Returns a grounded answer drawn from the indexed handbook sections.
    If the vector store has not been built yet, returns a safe degradation
    message instead of raising an exception.

    Args:
        query: The question to answer (in any language; model handles translation).

    Returns:
        A plain-text answer with source context, or a degradation message.
    """
    persist_dir = _get_persist_dir()

    if not Path(persist_dir).exists():
        return (
            "The resident handbook knowledge base is not available yet. "
            "Please ask a management staff member for assistance."
        )

    try:
        engine = _build_query_engine(persist_dir)
        response = engine.query(query)
        return str(response)
    except Exception as exc:  # pragma: no cover — surface runtime errors safely
        return (
            f"Could not retrieve an answer from the handbook at this time "
            f"({type(exc).__name__}). Please contact the management office."
        )
