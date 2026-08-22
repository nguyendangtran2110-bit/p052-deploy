"""
LangGraph nodes for the RAG chatbot workflow.
"""

from __future__ import annotations

from src.agents.state import AgentState
from src.services.groq_llm import generate_rag_answer
from src.services.rag import retrieve_context

FALLBACK_TEXT = (
    "Thông tin hiện có chưa đủ để xác định chính xác câu trả lời. "
    "Vui lòng liên hệ Ban Quản Lý tòa nhà để được hỗ trợ."
)


async def retrieve_node(state: AgentState) -> dict:
    """Retrieve relevant chunks from the resident handbook vector store."""
    query = state.get("query", "")
    try:
        chunks = retrieve_context(query, top_k=5)
        return {"retrieved_chunks": [c.to_dict() for c in chunks]}
    except Exception as exc:
        return {"error": str(exc), "retrieved_chunks": []}


async def generate_node(state: AgentState) -> dict:
    """Generate answer from context using Groq / Qwen LLM."""
    query = state.get("query", "")
    chunks = state.get("retrieved_chunks", [])
    history = state.get("chat_history", [])

    try:
        response = generate_rag_answer(query, chunks, history)
        return {
            "rag_response": response.model_dump(),
            "response": response.answer,
        }
    except Exception as exc:
        return {"error": str(exc)}


async def format_node(state: AgentState) -> dict:
    """Finalize and format response for downstream consumers."""
    rag_response = state.get("rag_response", {})
    answer = state.get("response") or rag_response.get("answer", "")
    return {"response": answer}


async def fallback_node(state: AgentState) -> dict:
    """Fallback handler when no chunks found or retrieval fails."""
    return {"response": FALLBACK_TEXT}
