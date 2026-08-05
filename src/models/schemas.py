from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="Tin nhắn từ user")


class ChatResponse(BaseModel):
    response: str = Field(..., description="Phản hồi từ agent")
    analysis: str = Field(default="", description="Phân tích nội bộ")


class DemoChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    actor_role: Literal["resident", "manager"]


class DraftRequest(DemoChatRequest):
    pass


class SubmitDraftRequest(BaseModel):
    actor_role: Literal["resident", "manager"]


class TicketUpdateRequest(BaseModel):
    actor_role: Literal["resident", "manager"]
    status: Literal["APPROVED", "REJECTED", "IN_PROGRESS", "RESOLVED"]
    note: str | None = Field(default=None, max_length=2000)
    assigned_manager: str | None = Field(default=None, max_length=120)


class ManagerActionRequest(BaseModel):
    actor_role: Literal["manager"]
