#!/usr/bin/env python3
"""Interactive terminal RAG chatbot with streaming output."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Prefer project .env over exported shell placeholders for local CLI usage.
load_dotenv(ROOT / ".env", override=True)

from src.services.groq_llm import citations_from_chunks, confidence_from_chunks, stream_rag_answer  # noqa: E402
from src.services.rag import retrieve_context  # noqa: E402

FALLBACK_TEXT = (
    "Xin lỗi, tôi không tìm thấy thông tin liên quan trong Sổ Tay Cư Dân. "
    "Vui lòng liên hệ Ban Quản Lý tòa nhà để được hỗ trợ."
)
CHUNK_PREVIEW_LIMIT = 420


def _chunk_preview(text: str) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= CHUNK_PREVIEW_LIMIT:
        return normalized
    return f"{normalized[:CHUNK_PREVIEW_LIMIT].rstrip()}..."


def _print_sources(chunks: list[dict]) -> None:
    citations = citations_from_chunks(chunks)
    if citations:
        print("\n\nNguồn tham khảo:")
        for index, citation in enumerate(citations, 1):
            ref = f"  {index}. {citation.source_file}"
            if citation.page_number:
                ref += f", trang {citation.page_number}"
            if citation.section_title:
                ref += f" - {citation.section_title}"
            print(ref)

    confidence = confidence_from_chunks(chunks)
    print(f"\nĐộ tin cậy ước tính: {confidence:.0%}")

    print(f"\nChunks đã retrieve ({len(chunks)}):")
    for index, chunk in enumerate(chunks, 1):
        source = chunk.get("source_file", "unknown")
        page = chunk.get("page_number", 0)
        section = chunk.get("section_title", "")
        score = chunk.get("score", 0.0)

        header = f"  Chunk {index}. {source}"
        if page:
            header += f", trang {page}"
        if section:
            header += f" - {section}"
        if score:
            header += f" | score={score:.4f}"

        print(header)
        print(f"    {_chunk_preview(chunk.get('text', ''))}")


def main() -> int:
    print("RAG Chatbot Phú Đông Sky Garden")
    print("Nhập câu hỏi để chat. Gõ /exit để thoát, /clear để xoá lịch sử.\n")

    chat_history: list[dict] = []

    while True:
        try:
            query = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTạm biệt.")
            return 0

        if not query:
            continue
        if query.casefold() in {"/exit", "/quit", "exit", "quit"}:
            print("Tạm biệt.")
            return 0
        if query.casefold() == "/clear":
            chat_history.clear()
            print("Đã xoá lịch sử hội thoại.\n")
            continue

        print("Đang tìm trong Sổ Tay Cư Dân...")
        chunks = [chunk.to_dict() for chunk in retrieve_context(query, top_k=5)]

        if not chunks:
            print(f"Bot: {FALLBACK_TEXT}\n")
            chat_history.extend([
                {"role": "user", "content": query},
                {"role": "assistant", "content": FALLBACK_TEXT},
            ])
            chat_history = chat_history[-12:]
            continue

        print("Bot: ", end="", flush=True)
        answer_parts: list[str] = []
        for token in stream_rag_answer(query, chunks, chat_history):
            print(token, end="", flush=True)
            answer_parts.append(token)

        answer = "".join(answer_parts).strip()
        _print_sources(chunks)
        print()

        chat_history.extend([
            {"role": "user", "content": query},
            {"role": "assistant", "content": answer},
        ])
        chat_history = chat_history[-12:]


if __name__ == "__main__":
    raise SystemExit(main())
