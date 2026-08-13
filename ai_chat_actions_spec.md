# AI Chat Actions Specification

## 1. Mục tiêu

Triển khai hai workflow AI có thể thực hiện trực tiếp trong đoạn chat:

1. **Resident assistant**: cư dân mô tả sự cố, Agent tự trích xuất dữ liệu, hỏi lại phần còn thiếu, cho xem bản nháp và sau khi cư dân xác nhận thì gọi tool tạo ticket.
2. **Manager assistant**: manager mô tả nội dung cần phát hành, Agent tự trích xuất dữ liệu, hỏi lại phần còn thiếu, cho xem bản nháp announcement và sau khi manager xác nhận thì tạo draft. Publish phải là một xác nhận riêng.

Cả hai workflow đều hỗ trợ upload file/ảnh trong chat. File được lưu qua S3 presigned URL; attachment ID được lưu trong workflow draft và cuối cùng liên kết vào ticket hoặc announcement.

## 2. Phạm vi và ranh giới

### 2.1. Trong phạm vi

- Chat nhiều lượt, có context theo conversation.
- Structured extraction từ message người dùng.
- Hỏi lại field bắt buộc còn thiếu.
- Preview trước khi thực hiện side effect.
- Confirmation và idempotency.
- Resident tạo ticket từ chatbot.
- Manager tạo draft announcement từ chatbot.
- Manager publish announcement sau một confirmation riêng.
- Attachment cho message/workflow object.
- SSE thông báo object được tạo/publish và message mới.
- RBAC JWT hiện tại.

### 2.2. Ngoài phạm vi MVP

- AI tự publish announcement mà không có confirmation.
- AI tự thay đổi status ticket sau khi tạo.
- AI tự archive announcement.
- Conversation riêng cho announcement sau khi publish.
- AI đọc nội dung file/ảnh bằng OCR hoặc vision model. MVP chỉ lưu và gắn attachment; extraction từ file là phase sau.
- Scheduled publish, email hàng loạt, Redis, outbox, WebSocket.
- Cho phép Agent thực hiện arbitrary database query hoặc arbitrary function call.

## 3. Thuật ngữ

| Thuật ngữ | Ý nghĩa |
| --- | --- |
| Conversation | Đoạn chat lâu dài. Resident ticket conversation vẫn gắn với ticket. Manager announcement conversation là chat riêng với assistant để tạo announcement. |
| Workflow | Một quy trình nghiệp vụ đang được Agent thu thập dữ liệu/thực hiện. |
| Draft | Dữ liệu đã trích xuất nhưng chưa thực hiện side effect hoặc chưa publish. |
| Action | Ý định thực hiện một tool có side effect. |
| Confirmation | Tín hiệu rõ ràng của người dùng cho phép thực hiện action. |
| Attachment ID | UUID metadata trong database; file binary nằm trên S3. |

## 4. Quy tắc nghiệp vụ chung

1. LLM/Agent chỉ được đề xuất action. Backend service mới là authority thực thi side effect.
2. Không tạo ticket/announcement khi chưa đủ required fields.
3. Không thực hiện side effect chỉ vì người dùng mô tả sự cố hoặc nội dung announcement.
4. Mọi action có side effect phải có confirmation rõ ràng, trừ các tool đọc dữ liệu.
5. Confirmation phải gắn với `workflow_id`, `workflow_version` và `action_id` hiện tại.
6. Retry cùng `action_id` không được tạo duplicate object.
7. Attachment phải thuộc actor hoặc workflow hiện tại; không được nhận attachment ID tùy ý của object khác.
8. Không tin các UUID, role, scope hoặc account ID do LLM tự sinh nếu không được backend validate.
9. Không đưa access token hoặc presigned URL vào prompt, message log hoặc Agent state persistent.
10. Khi thiếu thông tin, Agent hỏi một câu ngắn, ưu tiên hỏi các field có thể suy ra từ context trước.
11. Nếu câu trả lời mới thay đổi field đã thu thập, draft phải được cập nhật và preview phải phản ánh giá trị mới nhất.
12. Nếu người dùng từ chối hoặc đổi ý, workflow chuyển `cancelled`; không gọi tool.
13. Nếu conversation đang `management_active`, resident message không được quay lại Agent. Quy tắc này chỉ áp dụng ticket/resident conversation, không áp dụng manager assistant conversation.

## 5. Workflow state machine

```text
collecting
    | đủ required fields
    v
awaiting_confirmation
    | user confirms
    v
executing
    | success
    v
completed

collecting -> cancelled
awaiting_confirmation -> collecting       (user sửa thông tin)
awaiting_confirmation -> cancelled        (user hủy)
executing -> failed                        (tool/business error)
failed -> awaiting_confirmation            (retry sau khi refetch/resolve)
```

Announcement có thêm phase nghiệp vụ:

```text
announcement draft awaiting confirmation
    -> draft_created
    -> awaiting_publish_confirmation
    -> publishing
    -> published
```

`published` là terminal state của AI workflow. Archive dùng management lifecycle API thông thường.

## 6. Shared workflow contract

Agent phải trả structured result tương thích với contract sau. Tên field có thể map sang Python/Pydantic nhưng không được thay đổi ý nghĩa.

```json
{
  "workflow_id": "uuid",
  "workflow_type": "resident_ticket | manager_announcement",
  "state": "collecting | awaiting_confirmation | executing | completed | cancelled | failed | awaiting_publish_confirmation | publishing | published",
  "workflow_version": 4,
  "intent": "create_ticket | create_announcement | handbook_question | clarification",
  "assistant_message": "Cần biết sự cố xảy ra ở đâu?",
  "draft": {},
  "missing_fields": ["location"],
  "action": {
    "type": "ask_clarification | preview_ticket | create_ticket | preview_announcement | create_announcement_draft | publish_announcement | cancelled | completed",
    "action_id": "uuid",
    "requires_confirmation": true,
    "payload": {}
  },
  "attachment_ids": [],
  "citations": [],
  "error": null
}
```

### 6.1. Quy tắc field

- `missing_fields` luôn là mảng, rỗng khi đủ dữ liệu.
- `draft` chỉ chứa dữ liệu đã xác định hoặc có giá trị `null`; không tự điền dữ liệu demo.
- `action.payload` không được dùng làm nơi duy nhất lưu draft. Backend phải persist workflow draft.
- `workflow_version` tăng sau mỗi lần update state/draft hoặc thực thi action.
- `action_id` được tạo khi action chuyển sang trạng thái cần confirmation và giữ nguyên qua retry.
- `attachment_ids` là danh sách UUID đã được backend authorize; Agent không được tự tạo ID.

## 7. Resident ticket workflow

### 7.1. Required fields

Backend schema ticket hiện yêu cầu:

| Field | Bắt buộc | Nguồn ưu tiên |
| --- | --- | --- |
| `unit_id` | Có | Unit đã chọn trong resident profile/UI; không lấy tự do từ LLM |
| `category` | Có | Agent extraction, hỏi lại nếu không xác định |
| `priority` | Có | Agent đề xuất `medium` nếu không có dấu hiệu khác; cho resident sửa |
| `title` | Có | Agent tạo từ mô tả, resident có thể sửa |
| `description` | Có | Mô tả của resident |
| `location` | Có | Agent extraction, hỏi lại nếu thiếu |
| `attachment_ids` | Không | File upload trong workflow |

`priority` chỉ nhận `low`, `medium`, `high`, `urgent`. `category`, `title`, `description`, `location` phải được normalize và validate length bởi backend.

### 7.2. Luồng chuẩn

```text
Resident gửi message/attachment
    -> backend lưu user message + attachment
    -> Agent đọc conversation + workflow draft
    -> extract/merge ticket fields
    -> thiếu field: ask_clarification
    -> đủ field: preview_ticket
    -> resident confirm
    -> backend validate version/action/permission
    -> create_ticket tool gọi TicketService.create(source=chat)
    -> liên kết attachment IDs
    -> trả ticket + conversation ID
```

### 7.3. Confirmation

Các câu như “được”, “tạo đi”, “xác nhận” chỉ được xem là confirmation khi context hiện tại là `awaiting_confirmation` và action ID khớp. Không dùng keyword confirmation toàn cục.

Nếu resident trả lời sửa thông tin trong lúc preview, ví dụ “vị trí là ban công tầng 12”, Agent phải cập nhật draft rồi tạo preview mới; không tạo ticket ngay.

### 7.4. Kết quả thành công

```json
{
  "state": "completed",
  "action": {
    "type": "completed",
    "action_id": "uuid",
    "requires_confirmation": false,
    "payload": {
      "ticket_id": "uuid",
      "ticket_code": "TKT-..."
    }
  },
  "draft": {
    "ticket_id": "uuid"
  }
}
```

## 8. Manager announcement workflow

### 8.1. Required fields

| Field | Bắt buộc | Ghi chú |
| --- | --- | --- |
| `title` | Có | 2-255 ký tự |
| `content` | Có | 2-50000 ký tự |
| `type` | Có | Default `general`; enum backend |
| `priority` | Có | Default `normal`; enum backend |
| `scopes` | Có trước publish | Ít nhất một audience scope |
| `expires_at` | Không | Nếu có phải là thời gian hợp lệ/future khi publish |
| `attachment_ids` | Không | Tối đa theo backend |

Allowed `type`:

```text
general, maintenance, facility, regulation_update, event, emergency
```

Allowed `priority`:

```text
normal, important, urgent
```

Scope payload:

```json
{ "scope_type": "all_residents" }
{ "scope_type": "project", "project_code": "ONB" }
{ "scope_type": "building", "project_code": "ONB", "building": "A" }
{ "scope_type": "unit", "unit_id": "uuid" }
```

### 8.2. Luồng chuẩn

```text
Manager gửi message/attachment
    -> backend lưu manager message + attachment
    -> Agent đọc workflow draft
    -> extract/merge announcement fields
    -> thiếu field: ask_clarification
    -> đủ field/scope: preview_announcement
    -> manager confirm create draft
    -> create_announcement_draft tool
    -> state awaiting_publish_confirmation
    -> manager review draft
    -> manager confirm publish
    -> publish_announcement tool/API với version mới nhất
    -> state published
```

### 8.3. Publish confirmation

Tạo draft và publish là hai action khác nhau. Confirmation tạo draft không đồng nghĩa confirmation publish.

Agent phải hiển thị tối thiểu:

- title
- content
- type
- priority
- audience scopes
- expires_at
- danh sách attachment

Manager có thể yêu cầu chỉnh sửa giữa hai bước. Khi chỉnh sửa, version phải lấy từ backend; không publish bằng version cũ.

## 9. Attachment lifecycle

```text
POST /attachments/presign
    -> PUT binary to S3 upload_url
    -> retain attachment_id in workflow draft
    -> tool/service attaches IDs to ticket/announcement/message
    -> GET /attachments/{id}/download when user opens file
```

Quy tắc:

- MVP không cần Complete endpoint.
- Upload trước khi object tồn tại được phép nếu metadata attachment chưa có parent.
- Ticket tool phải attach IDs từ workflow draft, không chỉ IDs của message confirmation cuối.
- Announcement draft tool attach IDs vào announcement draft.
- Không cho attach một attachment đã thuộc object khác.
- Nếu upload thành công nhưng workflow bị hủy, attachment orphan cần được theo dõi bằng cleanup task phase sau; không tự xóa qua API chưa có.
- File/ảnh chỉ được lưu và hiển thị trong MVP; không tuyên bố Agent đã “đọc” nội dung file nếu chưa có extraction pipeline.

## 10. Authorization

| Action | Resident | Manager | Admin |
| --- | --- | --- | --- |
| Chat handbook | Có | Có thể dùng manager assistant tùy endpoint | Có |
| Create own ticket via chat | Có | Không qua resident workflow | Không thay resident |
| Read/update own ticket conversation | Có | Không phải resident flow | Có theo management API |
| Create announcement draft | Không | Có | Có |
| Publish own announcement | Không | Có | Có |
| Publish/archive announcement của manager khác | Không | Không | Có theo lifecycle API |

Role phải lấy từ JWT actor context/backend, không tin role trong prompt, body hoặc UI.

## 11. Error and conflict contract

| Tình huống | Kết quả |
| --- | --- |
| Thiếu field | `200` với `state=collecting`, `action=ask_clarification`; không tạo object |
| User hủy | `200` với `state=cancelled`; không side effect |
| Confirmation sai workflow/action | `409` hoặc business error; refetch workflow |
| Version cũ | `409`; giữ draft local, refetch và yêu cầu review |
| Attachment không thuộc workflow/actor | `403` hoặc `409` |
| Không đủ quyền | `403` |
| LLM/tool timeout | `failed` với retry an toàn; không đoán tool đã chạy |
| Tool đã chạy nhưng response timeout | Query bằng `action_id`/idempotency trước khi retry |
| Payload không hợp lệ | `422`, chỉ rõ field; không fallback demo |

## 12. Realtime

SSE event chỉ chứa metadata tối thiểu:

- `conversation.message.created`
- `conversation.handoff.changed`
- `ticket.created`
- `announcement.updated`
- `announcement.published`

Frontend nhận event thì refetch conversation/object bằng REST. Không gửi toàn bộ content announcement trong broadcast nếu audience bị giới hạn.

## 13. Acceptance criteria tổng thể

### Resident ticket

- Resident mô tả ticket trong một hoặc nhiều message.
- Agent hỏi lại từng field cần thiết còn thiếu.
- Agent không tạo ticket trước confirmation.
- Preview phản ánh đúng field và attachment.
- Confirm tạo đúng một ticket `source=chat`.
- Ticket gắn đúng conversation, unit và attachment.
- Retry không tạo duplicate.

### Manager announcement

- Manager mô tả announcement trong một hoặc nhiều message.
- Agent hỏi lại title/content/scope còn thiếu.
- Agent tạo draft sau confirmation.
- Agent không publish cùng confirmation tạo draft.
- Manager review/chỉnh sửa rồi xác nhận publish.
- Announcement publish đúng audience, attachment và version.
- Retry không tạo duplicate draft/publish.

### Cross-cutting

- JWT/RBAC được enforce ở backend.
- SSE cập nhật UI không cần F5.
- Không có ID demo trong real mode.
- Tests bao phủ happy path, missing fields, confirmation, attachment, permission, conflict và retry.

## 14. Thứ tự đọc và triển khai

Agent triển khai phải đọc file này trước, sau đó đọc:

1. `ai_chat_agent_spec.md`
2. `ai_chat_backend_spec.md`
3. `ai_chat_frontend_spec.md`

Nếu một spec layer mâu thuẫn file này, phải ưu tiên file này và cập nhật spec trước khi code.
