from uuid import uuid4

from fastapi import APIRouter, HTTPException

from src.agents.graph import agent, rag_agent
from src.models.schemas import (
    ChatRequest,
    ChatResponse,
    CitationSchema,
    DemoChatRequest,
    DraftRequest,
    ManagerActionRequest,
    RAGChatRequest,
    RAGChatResponse,
    RetrievedChunkSchema,
    SubmitDraftRequest,
    TicketUpdateRequest,
)
from src.services.mvp import mvp_service

router = APIRouter()


# ---------------------------------------------------------------------------
# RAG Chatbot endpoint (NEW)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Original endpoints (preserved)
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat với AI agent."""
    try:
        result = await agent.ainvoke({"query": request.message})
        return ChatResponse(
            response=result.get("response", ""),
            analysis=result.get("analysis", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def agent_status():
    """Kiểm tra trạng thái agent."""
    return {"status": "ready", "agent": "LangGraph Agent v1.0"}


@router.post("/chat/query")
async def demo_chat(request: DemoChatRequest):
    """Deterministic MVP chat: grounded-demo answer or draft notification."""
    detection = mvp_service.detect(request.message)
    if detection and request.actor_role == "resident":
        preview = mvp_service.preview_draft(request.message, detection)
        return {
            "answer": "Mình nhận thấy bạn đang báo một vấn đề có thể cần ban quản lý xử lý. Bạn có muốn tạo ticket không?",
            "notification": {"kind": "ticket_draft_available", "severity": detection["priority"]},
            "draft_preview": preview,
        }
    return {"answer": "Mình chưa tìm thấy thông tin đó trong tài liệu demo hiện có.", "citation": None}


@router.post("/ticket-drafts")
async def create_ticket_draft(request: DraftRequest):
    if request.actor_role != "resident":
        raise HTTPException(status_code=403, detail="Only residents can create ticket drafts")
    try:
        return mvp_service.create_draft(request.message)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/ticket-drafts/{draft_id}")
async def get_ticket_draft(draft_id: str):
    draft = mvp_service.get_draft(draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Ticket draft not found")
    return draft


@router.post("/ticket-drafts/{draft_id}/submit")
async def submit_ticket_draft(draft_id: str, request: SubmitDraftRequest):
    try:
        return {"ticket": mvp_service.submit_draft(draft_id, request.actor_role)}
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/tickets")
async def list_tickets():
    return {"tickets": mvp_service.tickets()}


@router.patch("/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, request: TicketUpdateRequest):
    try:
        return mvp_service.update_ticket(ticket_id, request.actor_role, request.status, request.note, request.assigned_manager)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/tickets/{ticket_id}/contact-resident")
async def contact_ticket_resident(ticket_id: str, request: ManagerActionRequest):
    try:
        return mvp_service.contact_resident(ticket_id, request.actor_role)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
__all__ = ["router", "api_router"]
