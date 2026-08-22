"""
LLM service with OpenAI primary and Qwen/Groq fallbacks for RAG generation.

This module handles the LLM generation step of the RAG pipeline:
- Takes retrieved chunks from ChromaDB as context
- Uses OpenAI first, then Qwen/DashScope and Groq via OpenAI-compatible clients
- Returns structured output via Pydantic models

Usage:
    from src.services.groq_llm import generate_rag_answer
    response = await generate_rag_answer("Giờ mở cửa hồ bơi?", chunks)
"""

from __future__ import annotations

from collections.abc import Iterator

from openai import OpenAI
from pydantic import BaseModel, Field

from src.config import get_settings

# ---------------------------------------------------------------------------
# PydanticAI Structured Output Schemas
# ---------------------------------------------------------------------------

class Citation(BaseModel):
    """A single citation referencing a source chunk."""
    source_file: str = Field(description="Tên file nguồn")
    page_number: int = Field(default=0, description="Số trang trong tài liệu")
    section_title: str = Field(default="", description="Tiêu đề mục/chương")
    relevance: str = Field(default="", description="Lý do trích dẫn chunk này")


class RAGResponse(BaseModel):
    """Structured response from the RAG pipeline."""
    answer: str = Field(description="Câu trả lời cho câu hỏi của cư dân")
    citations: list[Citation] = Field(default_factory=list, description="Danh sách nguồn trích dẫn")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Mức độ tự tin của câu trả lời (0-1)")


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Bạn là trợ lý AI thân thiện của chung cư Phú Đông Sky Garden. Hãy trả lời trực tiếp câu hỏi của cư dân bằng thông tin được cung cấp.

QUY TẮC:
1. Chỉ sử dụng thông tin trong các đoạn dữ liệu được cung cấp; không tự bịa chi tiết.
2. Không nhắc đến context, đoạn trích, hệ thống RAG, Sổ Tay Cư Dân hay quy trình tìm kiếm trong câu trả lời.
3. Trả lời bằng tiếng Việt, ngắn gọn, rõ ràng, lịch sự và đi thẳng vào nội dung.
4. Nếu thông tin chưa đủ để kết luận, nói tự nhiên rằng "Thông tin hiện có chưa đủ để xác định chính xác" và đề nghị cư dân liên hệ Ban Quản Lý.
5. Nếu câu hỏi liên quan đến khẩn cấp (cháy, rò rỉ gas, mất điện toàn tòa), nhắc nhở cư dân gọi hotline ngay.

ĐỊNH DẠNG TRẢ LỜI:
- Trả lời trực tiếp câu hỏi
- Chỉ nêu nguồn tham khảo khi người dùng yêu cầu hoặc khi nguồn giúp làm rõ câu trả lời
"""


def _has_usable_api_key(api_key: str) -> bool:
    """API keys are sent in HTTP headers, so reject placeholders and non-ASCII values early."""
    key = api_key.strip()
    if not key or key.startswith("your-"):
        return False
    return key.isascii()


def _chat_providers(settings) -> list[tuple[str, OpenAI, str]]:
    providers = []

    if _has_usable_api_key(settings.openai_api_key):
        providers.append((
            "openai",
            OpenAI(api_key=settings.openai_api_key.strip(), base_url=settings.openai_api_base),
            settings.model_name,
        ))

    if _has_usable_api_key(settings.qwen_api_key):
        providers.append((
            "qwen",
            OpenAI(api_key=settings.qwen_api_key.strip(), base_url=settings.qwen_api_base),
            settings.qwen_model_name,
        ))

    if _has_usable_api_key(settings.groq_api_key):
        providers.append((
            "groq",
            OpenAI(api_key=settings.groq_api_key.strip(), base_url=settings.groq_api_base),
            settings.groq_model_name,
        ))

    return providers


def _build_context_text(chunks: list[dict]) -> str:
    """Format retrieved chunks into context text for the LLM prompt."""
    if not chunks:
        return "Không có thông tin nào được tìm thấy trong sổ tay cư dân."

    parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("source_file", "unknown")
        page = chunk.get("page_number", 0)
        section = chunk.get("section_title", "")
        text = chunk.get("text", "")

        header = f"[Đoạn {i}] Nguồn: {source}"
        if page:
            header += f", Trang {page}"
        if section:
            header += f", Mục: {section}"

        parts.append(f"{header}\n{text}")

    return "\n\n---\n\n".join(parts)


def _extract_citations(chunks: list[dict]) -> list[Citation]:
    """Extract citation info from retrieved chunks."""
    citations = []
    seen = set()
    for chunk in chunks:
        source = chunk.get("source_file", "")
        page = chunk.get("page_number", 0)
        key = (source, page)
        if key not in seen:
            seen.add(key)
            citations.append(Citation(
                source_file=source,
                page_number=page,
                section_title=chunk.get("section_title", ""),
                relevance=chunk.get("text", "")[:100],
            ))
    return citations


def _estimate_confidence(chunks: list[dict]) -> float:
    """Estimate answer confidence from retrieved context availability."""
    if not chunks:
        return 0.1
    if len(chunks) >= 3:
        return 0.9
    if len(chunks) >= 1:
        return 0.7
    return 0.3


def _build_messages(
    query: str,
    chunks: list[dict],
    chat_history: list[dict] | None = None,
) -> list[dict]:
    """Build chat messages with RAG context and short conversation history."""
    context_text = _build_context_text(chunks)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if chat_history:
        for turn in chat_history[-6:]:
            messages.append({
                "role": turn.get("role", "user"),
                "content": turn.get("content", ""),
            })

    user_message = f"""CÂU HỎI CỦA CƯ DÂN:
{query}

THÔNG TIN TỪ SỔ TAY CƯ DÂN:
{context_text}"""

    messages.append({"role": "user", "content": user_message})
    return messages


def generate_rag_answer(
    query: str,
    chunks: list[dict],
    chat_history: list[dict] | None = None,
) -> RAGResponse:
    """
    Generate a RAG answer using OpenAI first, then Qwen/Groq as backups.

    Args:
        query: The user's question.
        chunks: Retrieved context chunks (list of dicts with text, source_file, etc.)
        chat_history: Optional conversation history for multi-turn context.

    Returns:
        RAGResponse with answer, citations, and confidence score.
    """
    settings = get_settings()
    providers = _chat_providers(settings)
    if not providers:
        return RAGResponse(
            answer="Lỗi cấu hình: cần thiết lập OPENAI_API_KEY, QWEN_API_KEY hoặc GROQ_API_KEY hợp lệ trong file .env.",
            citations=[],
            confidence=0.0,
        )

    messages = _build_messages(query, chunks, chat_history)
    last_error: Exception | None = None

    for provider_name, client, model_name in providers:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=settings.llm_temperature,
                max_tokens=1024,
            )

            if not response.choices:
                raise ValueError("LLM response did not include choices")

            answer_text = response.choices[0].message.content or ""
            citations = _extract_citations(chunks)

            return RAGResponse(
                answer=answer_text,
                citations=citations,
                confidence=_estimate_confidence(chunks),
            )

        except Exception as exc:
            last_error = exc
            print(f"[{provider_name}] LLM generation error: {type(exc).__name__}: {exc}")

    return RAGResponse(
        answer=(
            f"Xin lỗi, tôi không thể trả lời lúc này. Lỗi: {type(last_error).__name__}. "
            "Vui lòng thử lại sau hoặc liên hệ Ban Quản Lý."
        ),
        citations=[],
        confidence=0.0,
    )


def stream_rag_answer(
    query: str,
    chunks: list[dict],
    chat_history: list[dict] | None = None,
) -> Iterator[str]:
    """
    Stream a RAG answer token-by-token using OpenAI first, then Qwen/Groq as backups.

    This is intended for terminal or SSE-style consumers. It yields text
    chunks only; callers can use _extract_citations(chunks) after streaming
    to show sources.
    """
    settings = get_settings()
    providers = _chat_providers(settings)
    if not providers:
        yield "Lỗi cấu hình: cần thiết lập OPENAI_API_KEY, QWEN_API_KEY hoặc GROQ_API_KEY hợp lệ trong file .env."
        return

    messages = _build_messages(query, chunks, chat_history)
    last_error: Exception | None = None

    for provider_name, client, model_name in providers:
        emitted = False
        try:
            stream = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=settings.llm_temperature,
                max_tokens=1024,
                stream=True,
            )

            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = delta.content if delta else None
                if content:
                    emitted = True
                    yield content
            return
        except Exception as exc:
            last_error = exc
            print(f"[{provider_name}] Streaming error: {type(exc).__name__}: {exc}")
            if emitted:
                yield (
                    f"\n\nXin lỗi, phản hồi bị gián đoạn. Lỗi: {type(exc).__name__}. "
                    "Vui lòng thử lại sau hoặc liên hệ Ban Quản Lý."
                )
                return

    yield (
        f"Xin lỗi, tôi không thể trả lời lúc này. Lỗi: {type(last_error).__name__}. "
        "Vui lòng thử lại sau hoặc liên hệ Ban Quản Lý."
    )


def citations_from_chunks(chunks: list[dict]) -> list[Citation]:
    """Public helper for streaming callers that need citations after answer text."""
    return _extract_citations(chunks)


def confidence_from_chunks(chunks: list[dict]) -> float:
    """Public helper for streaming callers that need the same confidence heuristic."""
    return _estimate_confidence(chunks)
