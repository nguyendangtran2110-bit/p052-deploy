# Worklog — Team OnBxrd

> Ghi lại tất cả công việc đã làm theo ngày. Ai làm gì, kết quả gì.

---

## 2026-08-06

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Trần Đăng Nguyên | Formulate Data Ingestion architecture & plan | ✅ Done | [`ARCHITECTURE.md`](architecture/ARCHITECTURE.md) | 1h |
| Trần Đăng Nguyên | Build RAG Ingestion Pipeline (`ingest_handbook.py`) | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 2h |
| Trần Đăng Nguyên | Create RAG Retrieval Service (`rag.py`) | ✅ Done | [`src/services/rag.py`](../src/services/rag.py) | 1h |
| Trần Đăng Nguyên | Wire LangGraph Agent Tool (`search_knowledge`) | ✅ Done | [`src/agents/tools/example_tool.py`](../src/agents/tools/example_tool.py) | 0.5h |
| Trần Đăng Nguyên | Migrate to Qwen LLM (`qwen3.6-plus`) & Embeddings (`text-embedding-v4`) | ✅ Done | [`src/config.py`](../src/config.py), [`.env`](../.env) | 1h |
| Trần Đăng Nguyên | Resolve DashScope batch size limit & model metadata registration | ✅ Done | Fixed `embed_batch_size=10` & model dicts | 1h |
| Trần Đăng Nguyên | Create & run unit test suite | ✅ Done | 21/21 RAG tests passed | 0.5h |

**Tổng kết ngày:** Hoàn thành xây dựng và kiểm thử toàn bộ luồng RAG Ingestion Sổ tay cư dân trên nhánh `DataandIngestion`. Đã chuyển đổi thành công từ OpenAI sang Qwen `qwen3.6-plus` + `text-embedding-v4`, khắc phục giới hạn batch size của DashScope và xác minh kết quả query trực tiếp.

---

## 2026-08-07

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Trần Đăng Nguyên | Design Hybrid PDF OCR & Incremental Vector Store strategy | ✅ Done | `work_summary_2026-08-07.md` | 0.5h |
| Trần Đăng Nguyên | Implement PyMuPDF + Qwen3.6-Plus Hybrid PDF Loader & OCR Fallback | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 1.5h |
| Trần Đăng Nguyên | Upgrade vector store ingestion to Hash-based Incremental Upserting | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 1h |
| Trần Đăng Nguyên | Implement PDF-to-Markdown intermediate export (`export_pdf_to_markdown`) to `data/processed/` | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 0.5h |
| Trần Đăng Nguyên | Live ingestion test on real handbook (`so-tay-phu-dong-sky-garden.pdf`) | ✅ Done | 130 nodes indexed into ChromaDB | 1h |
| Trần Đăng Nguyên | Update & verify unit test suite (`tests/test_rag/`) | ✅ Done | 26/26 RAG unit tests passed (100% green) | 0.5h |

**Tổng kết ngày:** Đã tích hợp thành công cơ chế Hybrid PDF loader (sử dụng PyMuPDF trích xuất text nguyên bản và fallback tự động sang Qwen3.6-Plus Vision OCR cho PDF dạng ảnh/quét). Nâng cấp hệ thống Vector Store sang mô hình Incremental Upsert dựa trên document hash SHA-256 để bỏ qua các file không thay đổi, hỗ trợ xuất file Markdown trung gian (`data/processed/`) và thêm tùy chọn CLI `--export-md` & `--force-rebuild`. Đã nghiệm thu thực tế trên sổ tay cư dân 59 trang (130 nodes) và vượt qua 26/26 unit tests.

---

## 2026-08-10

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Trần Đăng Nguyên | Synchronize & Align Specs ([`Brief.md`](Brief.md), [`PRD.md`](PRD.md), [`WORKLOG.md`](WORKLOG.md)) | ✅ Done | Aligned Qwen models, KPIs, & removed legacy MoveIn name | 0.5h |
| Trần Đăng Nguyên | Implement OCR Quality Engine (`evaluate_ocr_quality()`) | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 1h |
| Trần Đăng Nguyên | Implement Markdown Audit Header Annotations (`export_pdf_to_markdown`) | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 0.5h |
| Trần Đăng Nguyên | Build 2-Stage HITL Audit CLI (`--export-only` & `--audit`) | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 0.5h |
| Trần Đăng Nguyên | Build Synthetic Scanned PDF Generator (`generate_sample_scanned_pdf.py`) | ✅ Done | [`data/raw/handbook_scanned_sample.pdf`](../data/raw/handbook_scanned_sample.pdf) | 0.5h |
| Trần Đăng Nguyên | Expand unit test suite & verify | ✅ Done | 31/31 RAG unit tests passed (100% green) | 0.5h |

**Tổng kết ngày:** Chi tiết xem tại `work_summary_2026-08-10.md`. Đã đồng bộ hóa toàn bộ tài liệu dự án với kiến trúc thực tế (Qwen `qwen3.6-plus`, `text-embedding-v4`, ChromaDB). Xây dựng hệ thống OCR Quality Gate tự động phát hiện lỗi nhiễu ký tự và thiếu từ; đính kèm header cảnh báo audit (`<!-- AUDIT_REQUIRED: ... -->`) vào file Markdown trung gian (`data/processed/`); hỗ trợ workflow HITL 2 giai đoạn thông qua tùy chọn CLI `--export-only` và `--audit`. Xây dựng bộ tạo PDF giả lập ảnh quét lỗi và kiểm thử thành công. Toàn bộ 31/31 unit tests đạt 100% green.

---

## 2026-08-11

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Trần Đăng Nguyên | Fix resource leak — `pdf_doc.close()` in `finally` block | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 0.5h |
| Trần Đăng Nguyên | Implement Chroma Dual-Mode client (local persistent / Docker HTTP) | ✅ Done | [`src/services/rag.py`](../src/services/rag.py) | 1h |
| Trần Đăng Nguyên | Multi-Tenant Metadata Filtering (`building_id` stamp + `MetadataFilters`) | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py), [`src/services/rag.py`](../src/services/rag.py), [`src/agents/tools/example_tool.py`](../src/agents/tools/example_tool.py) | 1.5h |
| Trần Đăng Nguyên | Complex Table Parsing — `extract_page_tables_as_markdown()` via PyMuPDF `find_tables()` | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 1h |
| Trần Đăng Nguyên | Expand unit test suite (Dual-Mode, Multi-Tenant, Table Parsing) | ✅ Done | 38/38 RAG tests passed | 0.5h |
| Trần Đăng Nguyên | Project Status & Missing Items Register documented | ✅ Done | [`work_summary_2026-08-11.md`](../work_summary_2026-08-11.md) | 0.5h |
| Nguyễn Minh Hiếu | Tái cấu trúc & hoàn thiện PRD (`PRD.md`) và Brief (`Brief.md`) | ✅ Done | [`PRD.md`](PRD.md), [`Brief.md`](Brief.md) | 1.5h |
| Nguyễn Minh Hiếu | Mô-đun hóa kiến trúc hệ thống, bổ sung ADR-0001 -> ADR-0014 và Review documents | ✅ Done | [`architecture/`](architecture/) | 2h |
| Nguyễn Minh Hiếu | Xây dựng bộ tài liệu kỹ thuật Frontend (Spec, Route Map, Component Map, Accessibility, State Matrix) | ✅ Done | [`frontend/`](frontend/) | 1.5h |
| Nguyễn Minh Hiếu | Dọn dẹp tài liệu cũ (`DESIGN.md`, `PRODUCT.md`) & cập nhật environment configuration | ✅ Done | [`.gitignore`](../.gitignore), [`.dockerignore`](../.dockerignore) | 0.5h |
| Nguyễn Minh Hiếu | Commit, Push branch `ender/develop` và cập nhật Pull Request #9 vào `main` với mô tả chi tiết | ✅ Done | [PR #9](https://github.com/AI20K-Build-Phase-Cohort-3/P-052/pull/9) | 0.5h |

**Tổng kết ngày:** Nguyễn Minh Hiếu hoàn thành tái cấu trúc toàn bộ tài liệu dự án (PRD, Brief, kiến trúc mô-đun hóa `architecture/`, 14 ADRs, specs Frontend) và tạo PR #9 vào `main`. Trần Đăng Nguyên hoàn thành nâng cấp RAG pipeline: sửa resource leak PyMuPDF, hỗ trợ ChromaDB Dual-Mode, lọc Multi-Tenant `building_id`, tích hợp Complex Table Parsing (PyMuPDF `find_tables()`), và mở rộng bộ unit test đạt 38/38 passed (100% green).

---

## 2026-08-12

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Trần Đăng Nguyên | Git pull main & stash resolution (`docs/Worklog.md` merge) | ✅ Done | [`docs/Worklog.md`](Worklog.md) | 0.5h |
| Trần Đăng Nguyên | Fix log path sanitization (`_sanitize_paths`) in `scripts/log_antigravity.py` | ✅ Done | [`scripts/log_antigravity.py`](../scripts/log_antigravity.py) | 0.5h |
| Trần Đăng Nguyên | Exclude `data/processed/` intermediate files from default ingestion discovery | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 0.5h |
| Trần Đăng Nguyên | Fix DashScope embedding token overflow via `SentenceSplitter` sub-chunking | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 1h |
| Trần Đăng Nguyên | Fix ChromaDB metadata scalar constraint (`warning_flags` list -> string) | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 0.5h |
| Trần Đăng Nguyên | Live vector ingestion into ChromaDB (167 nodes indexed successfully) | ✅ Done | `./data/chroma` | 0.5h |
| Trần Đăng Nguyên | Document daily progress & session summary | ✅ Done | [`work_summary_2026-08-12.md`](../work_summary_2026-08-12.md) | 0.5h |

**Tổng kết ngày:** Trần Đăng Nguyên thực hiện pull và đồng bộ nhánh `main` (tài liệu kiến trúc & ADRs mới), giải quyết xung đột `Worklog.md`. Khắc phục triệt me các lỗi RAG Ingestion: loại bỏ trùng lặp file xuất intermediate `data/processed/` (giảm từ 7 xuống 4 file nguồn), sub-chunking Markdown nodes bằng `SentenceSplitter(chunk_size=512)` xử lý dứt điểm lỗi token overflow API DashScope, và chuyển đổi `warning_flags` sang kiểu string tương thích chuẩn metadata ChromaDB. Đã nhúng và lưu trữ thành công toàn bộ 167 vector nodes vào ChromaDB, vượt qua 38/38 unit tests (100% green).

---

## 2026-08-13

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Trần Đăng Nguyên | Fix resource leak & `UnboundLocalError` guard in `load_pdf_document_hybrid()` | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 0.5h |
| Trần Đăng Nguyên | Fix directory path exclusion scope for explicit `--dir` target scanning | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 0.5h |
| Trần Đăng Nguyên | Complete metadata fields on `SimpleDirectoryReader` fallback loader path | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 0.5h |
| Trần Đăng Nguyên | Simplify `warning_flags` producer/consumer string contract & update unit test | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py), [`tests/test_rag/test_ingestion.py`](../tests/test_rag/test_ingestion.py) | 0.5h |
| Trần Đăng Nguyên | Author RAG Data Ingestion Pipeline & HITL Audit specification document | ✅ Done | [`docs/architecture/ingestion-pipeline.md`](architecture/ingestion-pipeline.md) | 1.5h |
| Trần Đăng Nguyên | Update Architecture index Document Map | ✅ Done | [`docs/architecture/README.md`](architecture/README.md) | 0.5h |
| Trần Đăng Nguyên | Log prompts & submit AI logs (`submit_log.py` → 202 Success) | ✅ Done | `.ai-log/` | 0.5h |
| Trần Đăng Nguyên | Document daily progress & session summary | ✅ Done | [`work_summary_2026-08-13.md`](../work_summary_2026-08-13.md) | 0.5h |

**Tổng kết ngày:** Trần Đăng Nguyên hoàn thành tối ưu hóa và sửa lỗi triệt để cho RAG Ingestion Pipeline: khắc phục resource leak `pdf_doc.close()` tránh nuốt lỗi khi mở file hỏng, sửa logic quét thư mục `--dir` tùy chỉnh, đồng bộ hóa đầy đủ 9 trường metadata cho luồng fallback `SimpleDirectoryReader`, chuẩn hóa hợp đồng dữ liệu `warning_flags` dạng string và cập nhật unit test. Xây dựng toàn bộ tài liệu kiến trúc kỹ thuật chuẩn [`ingestion-pipeline.md`](architecture/ingestion-pipeline.md) quy định chi tiết sơ đồ luồng, bảng schema metadata ChromaDB và quy trình HITL Audit 2 giai đoạn. Thực hiện log và submit thành công 13 nhật ký tương tác lên server (HTTP 202), toàn bộ 38/38 unit tests đạt 100% green.

---

## 2026-08-22

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Trần Đăng Nguyên | Tích hợp ChromaDB Vector Store vào `KnowledgeSearchService` thay thế mock `.md` | ✅ Done | [`src/backend/application/knowledge/search.py`](../src/backend/application/knowledge/search.py) | 1.5h |
| Trần Đăng Nguyên | Xây dựng hạ tầng Chatbot Session Logger (JSONL telemetry) | ✅ Done | [`src/backend/infrastructure/logging/session_logger.py`](../src/backend/infrastructure/logging/session_logger.py), [`data/logs/chat_sessions/`](../data/logs/chat_sessions/) | 1.5h |
| Trần Đăng Nguyên | Tích hợp Session Logger & Multi-turn Contextual Query Retrieval vào `ChatService` | ✅ Done | [`src/backend/application/chat/service.py`](../src/backend/application/chat/service.py) | 1h |
| Trần Đăng Nguyên | Sửa lỗi Webpack/Fontsource và tối ưu hóa Next.js 15 frontend build | ✅ Done | [`frontend/next.config.ts`](../frontend/next.config.ts), [`frontend/package.json`](../frontend/package.json) | 1h |
| Trần Đăng Nguyên | Cấu hình SQLite local dev, cơ chế in mã OTP ra console và script seed tài khoản demo | ✅ Done | [`scripts/seed_demo_accounts.py`](../scripts/seed_demo_accounts.py), [`src/backend/infrastructure/email/service.py`](../src/backend/infrastructure/email/service.py) | 1h |
| Trần Đăng Nguyên | Viết bộ kiểm thử `test_session_logger.py` và chạy full test suite (114/114 passed) | ✅ Done | [`tests/test_backend/test_session_logger.py`](../tests/test_backend/test_session_logger.py) | 0.5h |

**Tổng kết ngày:** Đã hoàn thành chuyển đổi toàn diện chatbot từ mock file `.md` sang truy vấn trực tiếp vector chunks trong ChromaDB (`so-tay-phu-dong-sky-garden.pdf`) kèm số trang chính xác. Xây dựng hệ thống ghi log phiên chat (`SessionLogger`) xuất dữ liệu JSONL hàng ngày tại `data/logs/chat_sessions/` phục vụ đo lường latency, retrieval score và intent tracking. Hoàn thiện script seed tài khoản demo (`resident@onbxrd.vn` / `admin@onbxrd.vn`) trên nền tảng SQLite local, khắc phục triệt để lỗi build frontend Next.js 15 và xác nhận toàn bộ 114/114 unit & integration tests đạt 100% green.

---

## 2026-08-23

| Member | Task | Status | Output | Time |
|--------|------|--------|--------|------|
| Trần Đăng Nguyên | Sửa lỗi DashScope Thinking Mode & LLM Structured Output (`enable_thinking: False`) | ✅ Done | [`src/agents/graph.py`](../src/agents/graph.py) | 1h |
| Trần Đăng Nguyên | Tích hợp Qdrant Cloud Vector Store & cơ chế Dual-Store Auto-Detection trong RAG | ✅ Done | [`src/services/rag.py`](../src/services/rag.py), [`src/backend/core/config.py`](../src/backend/core/config.py) | 1.5h |
| Trần Đăng Nguyên | Nâng cấp Handbook Ingestion CLI hỗ trợ `--store` (Qdrant & Chroma) | ✅ Done | [`scripts/ingest_handbook.py`](../scripts/ingest_handbook.py) | 1h |
| Trần Đăng Nguyên | Cấu hình Docker Compose environment pass-through và bổ sung Makefile lifecycle | ✅ Done | [`docker-compose.yml`](../docker-compose.yml), [`Makefile`](../Makefile), [`.env.example`](../.env.example) | 0.5h |
| Trần Đăng Nguyên | Viết unit test `TestQdrantMode` và chạy full regression test (150/150 passed) | ✅ Done | [`tests/test_rag/test_rag_service.py`](../tests/test_rag/test_rag_service.py) | 0.5h |
| Trần Đăng Nguyên | Chạy benchmark đánh giá guardrail Chatbot với DeepEval (83% pass rate) | ✅ Done | [`scripts/evaluate_deepeval_chatbot.py`](../scripts/evaluate_deepeval_chatbot.py), `eval/deepeval-results.json` | 0.5h |

**Tổng kết ngày:** Khắc phục triệt để lỗi gọi mô hình Qwen DashScope khi sử dụng function calling bằng cách vô hiệu hóa thinking mode (`extra_body={"enable_thinking": False}`), giúp Chatbot trả lời câu hỏi tự nhiên bằng tiếng Việt thay vì dump raw text chunk. Tích hợp hoàn chỉnh vector database **Qdrant Cloud** với cơ chế tự động nhận diện (Dual-Store Auto-Detection), đảm bảo môi trường local tiếp tục hoạt động mượt mà với ChromaDB mà không gây breaking change. Nâng cấp script ingestion sổ tay cư dân `--store qdrant` tự động khởi tạo collection và đồng bộ embeddings lên cloud. Bổ sung các lệnh đóng gói Docker trong `Makefile`, viết unit test cho Qdrant mode và đạt kết quả kiểm thử **150/150 unit & integration tests passed (100% green)** cùng với 83% pass rate trên bộ 100 test cases DeepEval.










