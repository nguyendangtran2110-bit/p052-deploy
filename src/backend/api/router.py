from fastapi import APIRouter

from src.backend.api.routes import (
    announcements,
    ai_workflows,
    attachments,
    auth,
    chat,
    conversations,
    knowledge,
    management,
    realtime,
    residents,
    tickets,
    units,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(announcements.resident_router)
api_router.include_router(announcements.management_router)
api_router.include_router(ai_workflows.router)
api_router.include_router(ai_workflows.workflow_router)
api_router.include_router(attachments.router)
api_router.include_router(realtime.router)
api_router.include_router(management.router)
api_router.include_router(chat.router)
api_router.include_router(conversations.router)
api_router.include_router(tickets.router)
api_router.include_router(knowledge.router)
api_router.include_router(residents.router)
api_router.include_router(units.router)


@api_router.get("/status", tags=["system"])
async def status():
    return {"status": "ready", "agent": "LangGraph Agent", "api_version": "v1"}
