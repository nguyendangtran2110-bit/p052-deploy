from fastapi import APIRouter

from src.backend.api.routes import chat, knowledge, residents, tickets, units

api_router = APIRouter()
api_router.include_router(chat.router)
api_router.include_router(tickets.router)
api_router.include_router(knowledge.router)
api_router.include_router(residents.router)
api_router.include_router(units.router)


@api_router.get("/status", tags=["system"])
async def status():
    return {"status": "ready", "agent": "LangGraph Agent", "api_version": "v1"}
