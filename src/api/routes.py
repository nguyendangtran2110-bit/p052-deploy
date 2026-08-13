from fastapi import APIRouter, HTTPException

from src.agents.graph import agent
from src.models.schemas import ChatRequest, ChatResponse, DemoChatRequest, DraftRequest, ManagerActionRequest, SubmitDraftRequest, TicketUpdateRequest
from src.services.mvp import mvp_service

router = APIRouter()


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
    lowered = request.message.casefold()
    if "hồ bơi" in lowered or "pool" in lowered:
        return {"answer": "Hồ bơi mở cửa hàng ngày từ 06:00 đến 21:00.", "citation": "Resident Handbook · Section 4.2"}
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
