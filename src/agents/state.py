from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """State schema cho LangGraph RAG agent.

    Mỗi node đọc và ghi vào state này.
    total=False cho phép tất cả fields là optional.
    """

    # Input
    query: str                    # Câu hỏi từ user
    chat_history: list[dict]      # Lịch sử hội thoại

    # RAG Pipeline
    retrieved_chunks: list[dict]  # Chunks tìm được từ ChromaDB
    rag_response: dict            # Structured response từ Groq/Qwen (RAGResponse)

    # Output
    response: str                 # Final text response
    analysis: str                 # Backward-compatible analysis field

    # Error handling
    error: str
    metadata: dict
