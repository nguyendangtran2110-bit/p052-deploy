from uuid import uuid4

from fastapi import APIRouter, HTTPException

from src.agents.graph import rag_agent
from src.models.schemas import (
    CitationSchema,
    RAGChatRequest,
    RAGChatResponse,
    RetrievedChunkSchema,
)

router = APIRouter(tags=["rag"])


@router.post("/rag/chat", response_model=RAGChatResponse)
async def rag_chat(request: RAGChatRequest) -> RAGChatResponse:
    """RAG chatbot — trả lời câu hỏi cư dân dựa trên Sổ Tay Cư Dân.

    Uses:
    - Qwen embedding + ChromaDB for retrieval
    - Groq LLM with Qwen backup for answer generation
    - LangGraph for stateful flow management
    """
    session_id = request.session_id or str(uuid4())

    try:
        result = await rag_agent.ainvoke({
            "query": request.message,
            "chat_history": [],  # Can be extended with session persistence
        })

        rag_response = result.get("rag_response", {})
        citations_raw = rag_response.get("citations", [])
        citations = [CitationSchema(**c) if isinstance(c, dict) else c for c in citations_raw]
        retrieved_chunks = result.get("retrieved_chunks", [])
        chunks = [
            RetrievedChunkSchema(
                chunk_index=index,
                text=chunk.get("text", ""),
                source_file=chunk.get("source_file", ""),
                page_number=chunk.get("page_number", 0),
                section_title=chunk.get("section_title", ""),
                score=chunk.get("score", 0.0),
            )
            for index, chunk in enumerate(retrieved_chunks, 1)
        ]

        return RAGChatResponse(
            answer=rag_response.get("answer") or result.get("response", "Không có câu trả lời."),
            citations=citations,
            confidence=rag_response.get("confidence", 0.0),
            chunks_used=len(chunks),
            chunks=chunks,
            session_id=session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ["router"]
