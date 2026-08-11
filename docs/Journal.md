# Weekly Journal — Team P-052 (OnBxrd)

> Ghi lại mỗi tuần: học được gì, khó khăn gì, quyết định gì, kế hoạch tiếp.

---

## Week 1: 05/08/2026 - 11/08/2026

### Mục tiêu tuần này
- [x] Thiết lập kiến trúc RAG Ingestion Pipeline & Chuyển đổi LLM/Embedding sang Qwen (`qwen3.6-plus`, `text-embedding-v4`).
- [x] Xây dựng cơ chế Hybrid PDF Loader (PyMuPDF + Vision OCR Fallback), Incremental Upserting & Quality Audit.
- [x] Chuẩn hóa toàn bộ PRD, kiến trúc hệ thống (ARCHITECTURE-SPINE, ADRs), và tài liệu Frontend.
- [x] Hoàn thiện Pull Request #9 hợp nhất nhánh `ender/develop` vào `main`.

### Đã hoàn thành (Nguyễn Minh Hiếu & Team)
- Xây dựng hoàn chỉnh RAG Ingestion Pipeline với DashScope Qwen SDK & Vector Store ChromaDB.
- Phát triển Hybrid PDF OCR Fallback và hệ thống OCR Quality Gate kiểm lỗi quét tài liệu.
- Hoàn thành bộ 31/31 RAG unit tests (100% green).
- Tái cấu trúc tài liệu toàn dự án: PRD, Brief, 14 ADRs (`ADR-0001` đến `ADR-0014`), tài liệu review kiến trúc, và toàn bộ frontend design specifications (`docs/frontend/`).
- Đẩy nhánh `ender/develop` lên remote và tạo/cập nhật PR #9 vào `main`.

### Khó khăn & Giải pháp
| Khó khăn | Giải pháp | Kết quả |
|----------|-----------|---------|
| Giới hạn batch size và đăng ký metadata model của DashScope SDK | Cố định `embed_batch_size=10` và cập nhật từ điển model metadata trong config | Pipeline chạy ổn định, không lỗi batch |
| Tài liệu PDF sổ tay bị quét thành file ảnh chất lượng kém | Triển khai Hybrid PDF Loader với PyMuPDF fallback sang Qwen3.6-Plus Vision OCR | Xử lý thành công file sổ tay cư dân 59 trang (130 nodes) |
| Tài liệu dự án bị phân tán và thiếu tính mô-đun hóa | Shard tài liệu vào `docs/architecture/` và `docs/frontend/`, ban hành 14 ADRs chuẩn | Toàn bộ spec nhất quán, sẵn sàng cho giai đoạn dev |

### Bài học
- Thiết kế mô-đun hóa tài liệu và tách biệt các Decision Record (ADR) ngay từ đầu giúp việc triển khai code bám sát kiến trúc ban đầu.
- Tự động hóa kiểm thử OCR và có cơ chế cảnh báo Human-in-the-loop (HITL) giúp nâng cao độ tin cậy của dữ liệu đầu vào cho RAG.

### Kế hoạch tuần sau
- [ ] Triển khai các module backend theo PRD & ADRs đã duyệt (Auth, Resident Registry, Ticket Management).
- [ ] Xây dựng Frontend UI theo đúng `FRONTEND-SPEC.md`, `ROUTE-MAP.md` và `COMPONENT-MAP.md`.
- [ ] Tích hợp API giữa Backend FastAPI và LangGraph Agent Orchestrator.

---

