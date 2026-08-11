# ADR 001: Các Quyết Định Kiến Trúc Cốt Lõi (Architecture Decision Records)

> **Dự án:** OnBxrd (BDSO2O-10)
> **Giai đoạn:** Phase 2 (Thiết kế Kiến trúc — Tuần 2)
> **Trạng thái:** Accepted / Live Document

---

## 1. Context & Problem Statement (Bối cảnh & Bài toán)
Dự án **OnBxrd** cần xây dựng hệ thống trợ lý AI hỗ trợ cư dân bàn giao nhà và chăm sóc khách hàng. Hệ thống yêu cầu:
1. Xử lý câu hỏi dựa trên sổ tay cư dân chính xác (RAG).
2. Xử lý các luồng công việc có trạng thái (Stateful Agent Workflows) cho onboarding & tạo ticket sự cố.
3. Giao diện mượt mà hỗ trợ phản hồi dạng dòng (Streaming SSE).

## 2. Decision Log (Nhật Ký Quyết Định)

### 📊 Quyết định 1: Lựa chọn Framework AI Agent — LangGraph
- **Lựa chọn:** LangGraph (thay vì LangChain Sequential Chain hay AutoGen).
- **Lý do:**
  - Hỗ trợ State Machine rõ ràng (Nodes & Edges), dễ quản lý luồng hội thoại phức tạp.
  - Tích hợp sẵn Human-in-the-Loop (HITL) cho phép Ban quản lý duyệt thông tin trước khi gửi cư dân.
  - Hỗ trợ tốt Python async & streaming tokens.
- **Hệ quả:** Team cần làm quen với cách khai báo State schema trong LangGraph.

### 🔌 Quyết định 2: Lựa chọn Backend Framework — FastAPI
- **Lựa chọn:** FastAPI (thay vì Flask hay Django).
- **Lý do:** Hiệu năng cao (Asynchronous ASGI), tự động sinh tài liệu Swagger OpenAPI, hỗ trợ Server-Sent Events (SSE) mượt mà.
- **Hệ quả:** Dễ dàng tích hợp Pydantic validation cho request/response.

### 🗄️ Quyết định 3: Lựa chọn Engine RAG — LlamaIndex + ChromaDB
- **Lựa chọn:** LlamaIndex cho Document Parsing & Chunking; ChromaDB làm Vector Database local/in-memory.
- **Lý do:** LlamaIndex xử lý tài liệu sổ tay tòa nhà dạng PDF/Docx rất mạnh, trích dẫn chính xác trang/mục. ChromaDB nhẹ, dễ chạy với Docker mà không tốn chi phí host cloud.

### 💻 Quyết định 4: Lựa chọn Frontend Rendering — Next.js (App Router, Client-Side Chat UI)
- **Lựa chọn:** Next.js / React (Client-Side Rendering cho Chat Interface).
- **Lý do:** Tùy biến UI linh hoạt, hỗ trợ đọc SSE stream từ FastAPI để hiển thị chữ gõ từng từ (typewriter effect).

---

## 3. Quản lý Quyết định Mới (Future ADRs)
Khi có quyết định kiến trúc mới trong quá trình phát triển (ví dụ: đổi Vector DB, thêm Caching layer, tích hợp OAuth2), team sẽ tạo thêm file `adr-002-xxx.md` trong thư mục `docs/adr/`.
