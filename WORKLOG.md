# Worklog — Team [Tên Team]

> Ghi lại tất cả công việc đã làm theo ngày. Ai làm gì, kết quả gì.

---

## 2026-08-06

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Team | Formulate Data Ingestion architecture & plan | ✅ Done | [`ARCHITECTURE.md`](file:///c:/Users/truyk/OneDrive/Documents/P-052/ARCHITECTURE.md) | 1h |
| Team | Build RAG Ingestion Pipeline (`ingest_handbook.py`) | ✅ Done | [`scripts/ingest_handbook.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/scripts/ingest_handbook.py) | 2h |
| Team | Create RAG Retrieval Service (`rag.py`) | ✅ Done | [`src/services/rag.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/src/services/rag.py) | 1h |
| Team | Wire LangGraph Agent Tool (`search_knowledge`) | ✅ Done | [`src/agents/tools/example_tool.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/src/agents/tools/example_tool.py) | 0.5h |
| Team | Migrate to Qwen LLM (`qwen3.6-plus`) & Embeddings (`text-embedding-v4`) | ✅ Done | [`src/config.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/src/config.py), [`.env`](file:///c:/Users/truyk/OneDrive/Documents/P-052/.env) | 1h |
| Team | Resolve DashScope batch size limit & model metadata registration | ✅ Done | Fixed `embed_batch_size=10` & model dicts | 1h |
| Team | Create & run unit test suite | ✅ Done | 21/21 RAG tests passed | 0.5h |

**Tổng kết ngày:** Hoàn thành xây dựng và kiểm thử toàn bộ luồng RAG Ingestion Sổ tay cư dân trên nhánh `DataandIngestion`. Đã chuyển đổi thành công từ OpenAI sang Qwen `qwen3.6-plus` + `text-embedding-v4`, khắc phục giới hạn batch size của DashScope và xác minh kết quả query trực tiếp.

---

## 2026-08-07

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Team | Design Hybrid PDF OCR & Incremental Vector Store strategy | ✅ Done | [`implementation_plan.md`](file:///C:/Users/truyk/.gemini/antigravity-ide/brain/a6181b00-0a35-4b1d-80a5-855b7f6deebb/implementation_plan.md) | 0.5h |
| Team | Implement PyMuPDF + Qwen3.6-Plus Hybrid PDF Loader & OCR Fallback | ✅ Done | [`scripts/ingest_handbook.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/scripts/ingest_handbook.py) | 1.5h |
| Team | Upgrade vector store ingestion to Hash-based Incremental Upserting | ✅ Done | [`scripts/ingest_handbook.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/scripts/ingest_handbook.py) | 1h |
| Team | Implement PDF-to-Markdown intermediate export (`export_pdf_to_markdown`) to `data/processed/` | ✅ Done | [`scripts/ingest_handbook.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/scripts/ingest_handbook.py) | 0.5h |

**Tổng kết ngày:** Đã tích hợp thành công cơ chế Hybrid PDF loader (sử dụng PyMuPDF trích xuất text nguyên bản và fallback tự động sang Qwen3.6-Plus Vision OCR cho PDF dạng ảnh/quét). Nâng cấp hệ thống Vector Store sang mô hình Incremental Upsert dựa trên document hash SHA-256 để bỏ qua các file không thay đổi, hỗ trợ xuất file Markdown trung gian (`data/processed/`) và thêm tùy chọn CLI `--export-md` & `--force-rebuild`.


