# AI Tracing & Interaction Logs (Deliverable #4)

> **Dự án:** OnBxrd (BDSO2O-10)
> **Giai đoạn:** Phase 3 (Phát triển & Kiểm thử — Tuần 3-4)
> **Mục tiêu:** Lưu vết tương tác với LLM, minh chứng agent reasoning steps và tool calls phục vụ nộp bài BTC AI20K.

---

## 1. Phương Án Thiết Lập Logging (LangSmith Integration)

Cách nhanh nhất để ghi log tương tác với LLM là cấu hình LangSmith (chỉ cần set 3 biến môi trường trong `.env`):

```bash
# Biến môi trường LangSmith Tracing (.env)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxxxxxx
LANGCHAIN_PROJECT=onbxrd-ai20k-p052
```

---

## 2. Nhật Ký Tương Tác Mẫu (Sample Execution Logs)

### 🟢 Test Case 1: Tra cứu thông tin nội quy cư dân (RAG Query)
- **User Query:** "Phí quản lý chung cư là bao nhiêu 1m2?"
- **Agent Reasoning Execution Trace:**
```text
[INFO] 2026-08-11 10:00:00 - User Input: "Phí quản lý chung cư là bao nhiêu 1m2?"
[DEBUG] Node: intent_router -> Classified Intent: "rag_query"
[DEBUG] Node: retriever -> Querying ChromaDB with query_embedding...
[INFO] Vector Retriever found 2 relevant chunks (Score: 0.89)
       - Chunk 1: "Phí dịch vụ quản lý vận hành là 12.000 VNĐ/m2/tháng (chưa bao gồm VAT)..." [Source: So_tay_cu_dan.pdf, Page 8]
[DEBUG] Node: generator -> Invoking GPT-4o-mini with System Prompt + Retrieved Context...
[INFO] LLM Output: "Phí quản lý vận hành chung cư là 12.000 VNĐ/m2/tháng (chưa bao gồm VAT)."
[INFO] Citation attached: "Sổ tay cư dân, Mục 2.1 - Phí dịch vụ"
```

---

### 🟡 Test Case 2: Đăng ký ticket bảo trì qua Agent Tool Call
- **User Query:** "Bồn cầu nhà tôi bị tắc, hãy gọi thợ giúp"
- **Agent Reasoning Execution Trace:**
```text
[INFO] 2026-08-11 10:05:00 - User Input: "Bồn cầu nhà tôi bị tắc, hãy gọi thợ giúp"
[DEBUG] Node: intent_router -> Classified Intent: "create_ticket"
[INFO] Executing Tool: create_maintenance_ticket_tool(category="plumbing", priority="high")
[INFO] Tool Output: {"ticket_id": "TCK-9912", "status": "created"}
[DEBUG] Node: generator -> Formulating response confirmation...
[INFO] Response Sent: "Tôi đã gửi yêu cầu sửa chữa ống nước (Mã ticket: TCK-9912) tới Ban kỹ thuật. Kỹ thuật viên sẽ liên hệ trong 15 phút."
```

---

## 3. Danh Sách Minh Chứng Cần Nộp Cho BTC
- [ ] Link Dashboard LangSmith Tracing công khai hoặc ảnh chụp màn hình Tracing Details.
- [ ] File log dạng text `logs/ai-execution.log` (ghi nhận ít nhất 10 lượt hội thoại mẫu đại diện cho các tính năng).
