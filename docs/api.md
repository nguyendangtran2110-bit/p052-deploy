# Đặt Tả API System (API Specification)

> **Dự án:** OnBxrd (BDSO2O-10)
> **Giai đoạn:** Phase 2 (Thiết kế & Đặt tả — Tuần 2)
> **Base URL:** `http://localhost:8000/api/v1` (Dev) | `https://api.onbxrd.render.com/api/v1` (Prod)

---

## 1. Tổng Quan Endpoints

| Method | Endpoint | Mô tả | Phân quyền |
| :--- | :--- | :--- | :--- |
| `POST` | `/chat/completions` | Gửi câu hỏi cho AI Agent (Streaming SSE) | Public / Resident |
| `GET` | `/onboarding/checklist` | Lấy danh sách kiểm tra move-in của cư dân | Resident |
| `POST` | `/tickets` | Gửi yêu cầu hỗ trợ / báo sự cố mới | Resident |
| `GET` | `/tickets` | Lấy danh sách ticket của cư dân / BQL | Resident / Admin |
| `PATCH`| `/tickets/{ticket_id}/approve`| Duyệt ticket qua luồng Human-in-the-Loop | Admin / BQL |

---

## 2. Chi Tiết Endpoints chính

### 💬 2.1 Chat với AI Agent (Streaming Response)
- **Endpoint:** `POST /api/v1/chat/completions`
- **Headers:** `Content-Type: application/json`
- **Request Body:**
```json
{
  "resident_id": "res_12345",
  "query": "Quy định về thời gian chuyển đồ vào chung cư như thế nào?",
  "stream": true
}
```
- **Response Format (Server-Sent Events - SSE):**
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

data: {"token": "Theo ", "done": false}
data: {"token": "nội quy ", "done": false}
data: {"token": "tòa nhà, ", "done": false}
data: {"token": "thời gian chuyển đồ từ 8:00 - 17:00...", "done": false, "citations": ["Sổ tay cư dân Mục 3.2, Trang 15"]}
data: {"token": "", "done": true}
```

---

### 📋 2.2 Đăng Ký Ticket Sự Cố
- **Endpoint:** `POST /api/v1/tickets`
- **Request Body:**
```json
{
  "resident_id": "res_12345",
  "category": "plumbing",
  "title": "Rò rỉ nước đường ống bồn rửa bát",
  "description": "Nước bị rỉ từ khớp nối dưới bồn rửa",
  "urgency": "medium"
}
```
- **Response Format:**
```json
{
  "ticket_id": "TCK-2026-0811",
  "status": "pending_approval",
  "assigned_department": "Kỹ thuật tòa nhà",
  "created_at": "2026-08-11T09:30:00Z"
}
```

---

## 3. Mã Lỗi Chuẩn (Error Codes)
- `400 Bad Request`: Payload không đúng định dạng.
- `401 Unauthorized`: Mất Token xác thực.
- `429 Too Many Requests`: Vượt quá giới hạn gọi API (Rate limit).
- `500 Internal Server Error`: Lỗi LLM Provider hoặc Backend Server.
