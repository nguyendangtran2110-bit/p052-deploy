# RAG Chatbot Resident Handbook

> **Dự án:** OnBxrd / Phú Đông Sky Garden
> **Mục tiêu:** Chatbot trả lời câu hỏi cư dân dựa trên Sổ Tay Cư Dân, có nguồn tham khảo rõ ràng.

---

## 1. Tổng Quan

RAG chatbot cho phép cư dân hỏi các thông tin trong Sổ Tay Cư Dân, ví dụ:

- Giờ mở cửa hồ bơi.
- Quy định nhận bưu phẩm.
- Thông tin bộ phận vận hành, vệ sinh, tiện ích.
- Các nội quy sinh hoạt và sử dụng khu vực chung.

Luồng hiện tại:

```text
Resident Assistant UI
  -> Next.js API Proxy /api/rag/chat
  -> FastAPI /api/v1/rag/chat
  -> LangGraph RAG Agent
  -> ChromaDB retrieval
  -> Groq/Qwen answer generation
  -> Answer + citations + retrieved chunks
```

Frontend chỉ gọi same-origin `/api/rag/chat`; Next.js proxy sẽ chuyển request sang backend FastAPI. Cách này tránh lỗi CORS và giúp frontend không cần hard-code backend host.

---

## 2. Chức Năng Chính

### 2.1 Hỏi đáp theo Sổ Tay Cư Dân

Người dùng nhập câu hỏi ở trang:

```text
/resident/assistant
```

Chatbot trả lời bằng nội dung đã retrieve từ handbook. Nếu không tìm thấy context phù hợp, backend trả fallback an toàn hướng cư dân liên hệ Ban Quản Lý.

### 2.2 Hiển thị nguồn tham khảo

Response RAG có thể bao gồm:

- `citations`: nguồn do LLM format.
- `chunks`: các đoạn văn bản retrieval thực tế từ vector store.

Frontend ưu tiên hiển thị `citations`. Nếu không có citation, frontend fallback sang `chunks` để vẫn cho người dùng thấy nguồn được dùng.

Trên UI, phần `Approved sources` được thu gọn thành danh sách accordion. Người dùng click nút mũi tên để mở chi tiết từng nguồn.

### 2.3 Chat UI

Trang assistant hiện dùng layout dạng chatbot:

- Câu hỏi người dùng nằm bên phải.
- Câu trả lời chatbot nằm bên trái.
- Nhấn `Enter` để gửi.
- Nhấn `Shift + Enter` để xuống dòng.
- Sau khi gửi, ô nhập tự clear.

### 2.4 Session ID

Backend trả `session_id`. Frontend lưu session này trong state của trang và gửi lại ở câu tiếp theo. Hiện backend chưa persist chat history dài hạn, nhưng contract đã sẵn để mở rộng.

---

## 3. API Contract

### 3.1 Frontend Proxy

```http
POST /api/rag/chat
Content-Type: application/json
X-OnBxrd-Demo-Principal: <demo-account-id>
```

Request:

```json
{
  "message": "giờ mở cửa hồ bơi",
  "session_id": "optional-session-id"
}
```

Proxy yêu cầu principal là resident demo account. Nếu thiếu hoặc không phải resident, trả `401`.

### 3.2 Backend RAG Endpoint

```http
POST /api/v1/rag/chat
Content-Type: application/json
```

Request:

```json
{
  "message": "giờ mở cửa hồ bơi",
  "session_id": "optional-session-id"
}
```

Response:

```json
{
  "answer": "Hồ bơi mở cửa từ...",
  "citations": [
    {
      "source_file": "so-tay-phu-dong-sky-garden.pdf",
      "page_number": 17,
      "section_title": "Dịch vụ Hồ Bơi",
      "relevance": "Thời gian hoạt động..."
    }
  ],
  "confidence": 0.9,
  "chunks_used": 5,
  "chunks": [
    {
      "chunk_index": 1,
      "text": "Nội dung đoạn được retrieve...",
      "source_file": "so-tay-phu-dong-sky-garden.pdf",
      "page_number": 17,
      "section_title": "",
      "score": 0.5297
    }
  ],
  "session_id": "generated-or-reused-session-id"
}
```

---

## 4. Cách Chạy Local

### 4.1 Backend

```bash
cd /Users/raiju/P-052
uvicorn src.main:app --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

### 4.2 Frontend

```bash
cd /Users/raiju/P-052/frontend
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Mở:

```text
http://127.0.0.1:3000/login
```

Sau đó đăng nhập resident demo và vào:

```text
http://127.0.0.1:3000/resident/assistant
```

Nếu backend dùng host/port khác:

```bash
BACKEND_API_URL=http://127.0.0.1:8000 npm run dev -- --hostname 127.0.0.1 --port 3000
```

---

## 5. Các File Liên Quan

### Backend

| File | Vai trò |
| :--- | :--- |
| `src/main.py` | Khởi tạo FastAPI app, CORS, mount router dưới `/api/v1`. |
| `src/api/routes.py` | Định nghĩa endpoint `POST /api/v1/rag/chat`. |
| `src/models/schemas.py` | Pydantic schemas: `RAGChatRequest`, `RAGChatResponse`, `CitationSchema`, `RetrievedChunkSchema`. |
| `src/agents/graph.py` | Build LangGraph `rag_agent` gồm retrieve, generate, format, fallback. |
| `src/agents/nodes/rag_nodes.py` | Các node chính của RAG flow. |
| `src/services/rag.py` | Retrieval service dùng ChromaDB + LlamaIndex. |
| `src/services/groq_llm.py` | Sinh câu trả lời từ chunks bằng Groq/Qwen fallback. |
| `src/config.py` | Cấu hình API keys, model names, Chroma persist dir. |

### Frontend

| File | Vai trò |
| :--- | :--- |
| `frontend/app/(resident)/resident/assistant/page.tsx` | Trang chatbot UI cho cư dân. |
| `frontend/app/api/rag/chat/route.ts` | Next.js proxy route gọi FastAPI backend. |
| `frontend/src/lib/rag-api.ts` | Client helper gọi `/api/rag/chat`, sanitize và map response sang UI contract. |
| `frontend/src/lib/mock-llm.ts` | Giữ type `AssistantResult` và sanitizer dùng lại cho output RAG. |
| `frontend/src/styles/globals.css` | Style chat bubble, answer card, citation accordion. |

### Data & Ingestion

| File / Folder | Vai trò |
| :--- | :--- |
| `so-tay-phu-dong-sky-garden.pdf` | PDF handbook local, đang ignore khỏi git vì là data file. |
| `data/chroma/` | ChromaDB persist directory cho vector index. |
| `scripts/ingest_handbook.py` | Script ingest handbook vào vector store. |
| `scripts/rag_chat.py` | Script thử RAG chat từ terminal. |

### Tests

| File | Vai trò |
| :--- | :--- |
| `tests/test_api/test_routes.py` | Test backend route RAG trả chunk details. |
| `tests/test_rag/test_rag_service.py` | Test retrieval service. |
| `tests/test_rag/test_ingestion.py` | Test ingestion handbook. |
| `tests/test_rag/test_search_tool.py` | Test search/retrieval tool. |
| `frontend/tests/rag-api.test.ts` | Test frontend RAG client mapping và fallback. |

---

## 6. Lệnh Kiểm Tra

Backend:

```bash
pytest tests/test_api/test_routes.py::test_rag_chat_returns_retrieved_chunk_details
pytest tests/test_rag -q
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run lint
npm test -- rag-api routes
```

Manual end-to-end:

```bash
curl -X POST http://127.0.0.1:3000/api/rag/chat \
  -H 'Content-Type: application/json' \
  -H 'X-OnBxrd-Demo-Principal: demo-resident-lagoon' \
  --data '{"message":"giờ mở cửa hồ bơi"}'
```

Kết quả mong đợi: HTTP `200`, có `answer`, `citations` hoặc `chunks`, và `session_id`.

---

## 7. Ghi Chú Mở Rộng

- Nếu muốn có multi-turn context thật, cần persist `chat_history` theo `session_id` ở backend.
- Nếu muốn citation chính xác hơn, ưu tiên hiển thị metadata từ retrieved chunks thay vì để LLM tự diễn giải nguồn.
- Nếu deploy frontend/backend khác origin, giữ proxy `/api/rag/chat` và cấu hình `BACKEND_API_URL` trong môi trường frontend.
- Nếu vector store chưa có dữ liệu, chạy lại ingestion handbook trước khi demo.
