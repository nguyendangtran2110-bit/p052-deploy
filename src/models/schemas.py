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


# ---------------------------------------------------------------------------
# RAG Chatbot schemas
# ---------------------------------------------------------------------------

class RAGChatRequest(BaseModel):
    """Request body for RAG chatbot endpoint."""
    message: str = Field(..., min_length=1, max_length=5000, description="Câu hỏi của cư dân")
    session_id: str | None = Field(default=None, description="Session ID để track hội thoại")


class CitationSchema(BaseModel):
    """Citation reference from the handbook."""
    source_file: str = Field(default="", description="Tên file nguồn")
    page_number: int = Field(default=0, description="Số trang")
    section_title: str = Field(default="", description="Tiêu đề mục")
    relevance: str = Field(default="", description="Trích đoạn liên quan")


class RetrievedChunkSchema(BaseModel):
    """Retrieved context chunk used by the RAG chatbot."""
    chunk_index: int = Field(..., ge=1, description="Thứ tự chunk trong kết quả retrieval")
    text: str = Field(default="", description="Nội dung chunk")
    source_file: str = Field(default="", description="Tên file nguồn")
    page_number: int = Field(default=0, description="Số trang")
    section_title: str = Field(default="", description="Tiêu đề mục")
    score: float = Field(default=0.0, description="Điểm liên quan từ vector search")


class RAGChatResponse(BaseModel):
    """Response from RAG chatbot endpoint."""
    answer: str = Field(..., description="Câu trả lời")
    citations: list[CitationSchema] = Field(default_factory=list, description="Nguồn trích dẫn")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Độ tự tin (0-1)")
    chunks_used: int = Field(default=0, description="Số chunks được sử dụng")
    chunks: list[RetrievedChunkSchema] = Field(default_factory=list, description="Chi tiết các chunks đã retrieve")
    session_id: str | None = Field(default=None, description="Session ID")
