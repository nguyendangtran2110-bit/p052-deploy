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
| Team | Design Hybrid PDF OCR & Incremental Vector Store strategy | ✅ Done | [`work_summary_2026-08-07.md`](file:///c:/Users/truyk/OneDrive/Documents/P-052/work_summary_2026-08-07.md) | 0.5h |
| Team | Implement PyMuPDF + Qwen3.6-Plus Hybrid PDF Loader & OCR Fallback | ✅ Done | [`scripts/ingest_handbook.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/scripts/ingest_handbook.py) | 1.5h |
| Team | Upgrade vector store ingestion to Hash-based Incremental Upserting | ✅ Done | [`scripts/ingest_handbook.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/scripts/ingest_handbook.py) | 1h |
| Team | Implement PDF-to-Markdown intermediate export (`export_pdf_to_markdown`) to `data/processed/` | ✅ Done | [`scripts/ingest_handbook.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/scripts/ingest_handbook.py) | 0.5h |
| Team | Live ingestion test on real handbook (`so-tay-phu-dong-sky-garden.pdf`) | ✅ Done | 130 nodes indexed into ChromaDB | 1h |
| Team | Update & verify unit test suite (`tests/test_rag/`) | ✅ Done | 26/26 RAG unit tests passed (100% green) | 0.5h |

**Tổng kết ngày:** Đã tích hợp thành công cơ chế Hybrid PDF loader (sử dụng PyMuPDF trích xuất text nguyên bản và fallback tự động sang Qwen3.6-Plus Vision OCR cho PDF dạng ảnh/quét). Nâng cấp hệ thống Vector Store sang mô hình Incremental Upsert dựa trên document hash SHA-256 để bỏ qua các file không thay đổi, hỗ trợ xuất file Markdown trung gian (`data/processed/`) và thêm tùy chọn CLI `--export-md` & `--force-rebuild`. Đã nghiệm thu thực tế trên sổ tay cư dân 59 trang (130 nodes) và vượt qua 26/26 unit tests.

---

## 2026-08-10

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Team | Synchronize & Align Specs ([`Brief.md`](file:///c:/Users/truyk/OneDrive/Documents/P-052/docs/Brief.md), [`PRD.md`](file:///c:/Users/truyk/OneDrive/Documents/P-052/docs/PRD.md), [`WORKLOG.md`](file:///c:/Users/truyk/OneDrive/Documents/P-052/WORKLOG.md)) | ✅ Done | Aligned Qwen models, KPIs, & removed legacy MoveIn name | 0.5h |
| Team | Implement OCR Quality Engine (`evaluate_ocr_quality()`) | ✅ Done | [`scripts/ingest_handbook.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/scripts/ingest_handbook.py) | 1h |
| Team | Implement Markdown Audit Header Annotations (`export_pdf_to_markdown`) | ✅ Done | [`scripts/ingest_handbook.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/scripts/ingest_handbook.py) | 0.5h |
| Team | Build 2-Stage HITL Audit CLI (`--export-only` & `--audit`) | ✅ Done | [`scripts/ingest_handbook.py`](file:///c:/Users/truyk/OneDrive/Documents/P-052/scripts/ingest_handbook.py) | 0.5h |
| Team | Build Synthetic Scanned PDF Generator (`generate_sample_scanned_pdf.py`) | ✅ Done | [`data/raw/handbook_scanned_sample.pdf`](file:///c:/Users/truyk/OneDrive/Documents/P-052/data/raw/handbook_scanned_sample.pdf) | 0.5h |
| Team | Expand unit test suite & verify | ✅ Done | 31/31 RAG unit tests passed (100% green) | 0.5h |

**Tổng kết ngày:** Chi tiết xem tại [`work_summary_2026-08-10.md`](file:///c:/Users/truyk/OneDrive/Documents/P-052/work_summary_2026-08-10.md). Đã đồng bộ hóa toàn bộ tài liệu dự án với kiến trúc thực tế (Qwen `qwen3.6-plus`, `text-embedding-v4`, ChromaDB). Xây dựng hệ thống OCR Quality Gate tự động phát hiện lỗi nhiễu ký tự và thiếu từ; đính kèm header cảnh báo audit (`<!-- AUDIT_REQUIRED: ... -->`) vào file Markdown trung gian (`data/processed/`); hỗ trợ workflow HITL 2 giai đoạn thông qua tùy chọn CLI `--export-only` và `--audit`. Xây dựng bộ tạo PDF giả lập ảnh quét lỗi và kiểm thử thành công. Toàn bộ 31/31 unit tests đạt 100% green.



