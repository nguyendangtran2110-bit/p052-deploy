# AI Chat Frontend Specification

## 1. Mục tiêu

Nối UI Next.js hiện tại với AI workflow backend theo `ai_chat_actions_spec.md` và `ai_chat_backend_spec.md`.

Hai trải nghiệm:

- Resident chat: hỏi handbook hoặc tạo ticket bằng chatbot.
- Manager assistant: chat riêng để soạn draft announcement, review và publish.

Không trộn manager assistant vào màn hình resident handoff conversation. Handoff là luồng resident với manager; announcement assistant là luồng manager với Agent.

## 2. Resident chat

### 2.1. Route và context

Giữ route `/app/chat`.

- Lấy profile qua `GET /residents/me`.
- Resident chọn unit từ các unit thật trong profile.
- Không gửi `unit-a-1204` hoặc UUID giả.
- Conversation ID và workflow ID có thể lưu trong query:

  ```text
  /app/chat?conversation_id=<uuid>&workflow_id=<uuid>
  ```

- Khi refresh, gọi `GET /conversations/{id}` và `GET /ai/workflows/{id}` nếu có.
- Nếu không có ID, render chat mới, không seed demo messages khi `NEXT_PUBLIC_USE_MOCKS=false`.

### 2.2. Composer

Composer hỗ trợ:

- text message;
- multiple attachments trong giới hạn backend;
- MIME/size validation client-side;
- upload progress/state;
- remove attachment trước khi gửi;
- retry upload thất bại;
- disable submit trong lúc upload/send;
- Enter gửi, Shift+Enter xuống dòng.

Flow upload:

```text
file select
  -> POST /attachments/presign
  -> PUT file to S3 upload_url
  -> store attachment_id in composer/workflow state
  -> send message with attachment_ids
```

Không hiển thị presigned URL. Không coi upload thành công là message đã gửi thành công.

### 2.3. Rendering workflow states

| State/action | UI |
| --- | --- |
| `collecting` | Hiển thị câu hỏi Agent và draft summary nhỏ nếu có. |
| `ask_clarification` | Highlight field cần bổ sung, giữ attachments/draft. |
| `awaiting_confirmation` | Hiển thị preview ticket và nút “Xác nhận tạo ticket”. |
| `executing` | Disable confirm, hiển thị progress. |
| `completed` | Hiển thị ticket code/link tới `/app/tickets/{id}`. |
| `cancelled` | Hiển thị đã hủy và nút bắt đầu workflow mới. |
| `failed` | Hiển thị lỗi, giữ draft và nút thử lại an toàn. |
| `management_active` | Không gửi message vào Agent; hiển thị manager đang xử lý theo contract ticket hiện tại. |

Confirmation request phải gửi:

```json
{
  "workflow_id": "uuid",
  "workflow_version": 3,
  "confirmed_action_id": "uuid",
  "confirm_action": true,
  "idempotency_key": "uuid"
}
```

Không dùng text button state làm nguồn confirmation duy nhất.

### 2.4. Draft editing

MVP có thể cho resident sửa bằng message tự nhiên, ví dụ “vị trí là ban công”. Frontend giữ draft preview và render response mới sau mỗi lượt.

Không cho sửa trực tiếp các ID hệ thống. Unit phải đổi qua selector thật.

## 3. Manager assistant

### 3.1. Route

Thêm route:

```text
/management/assistant
/management/assistant/[conversationId]
```

Navigation thêm mục “AI announcement assistant” cho manager/admin. Không hiển thị cho resident/staff.

### 3.2. API

```http
POST /management/assistant/conversations
GET  /management/assistant/conversations/{conversation_id}
POST /management/assistant/conversations/{conversation_id}/messages
GET  /ai/workflows/{workflow_id}
POST /ai/workflows/{workflow_id}/cancel
```

React Query key:

```text
["management", "assistant", "conversations"]
["management", "assistant", "conversation", conversationId]
["ai-workflow", workflowId]
```

### 3.3. Manager composer

Tương tự resident composer nhưng context là announcement. Attachment được upload trước message và giữ trong workflow draft.

Manager có thể viết:

```text
“Soạn thông báo bảo trì thang máy tòa A vào ngày mai, mức quan trọng.”
```

Agent có thể hỏi lại:

- nội dung chi tiết;
- thời gian chính xác;
- audience scope;
- expiry;
- type/priority nếu chưa xác định.

### 3.4. Announcement preview

Preview phải hiển thị:

- title;
- content;
- type;
- priority;
- scope chi tiết;
- expires_at;
- attachments;
- workflow version;
- action ID.

Nút:

1. “Tạo draft” -> confirmation `create_announcement_draft`.
2. Sau khi draft thành công, hiển thị announcement code/id và nút “Review & publish”.
3. “Publish” -> confirmation riêng `publish_announcement` với version mới nhất.
4. “Chỉnh sửa” -> gửi message hoặc chuyển form edit draft.
5. “Hủy” -> cancel workflow.

Không có nút publish tự động sau khi create draft response.

## 4. Attachment UI

### 4.1. Common component

Tạo component dùng chung, ví dụ:

```text
frontend/src/components/chat-attachments.tsx
frontend/src/features/ai-chat/attachment-uploader.ts
```

Component chịu trách nhiệm:

- chọn nhiều file;
- validate MIME/size;
- upload presigned;
- progress/error/retry;
- preview ảnh local trước upload;
- render file name/size;
- remove khỏi draft trước action;
- download attachment sau message/object response.

### 4.2. Message attachments

- User message render attachment IDs sau khi backend response/refetch.
- Assistant/manager message có thể hiển thị file metadata nếu backend trả metadata; không hiển thị raw ID như UI chính.
- Download gọi `GET /attachments/{id}/download`, sau đó mở URL.
- Khi upload xong nhưng send message thất bại, giữ pending attachment IDs và cho retry; không gửi lại binary tự động nếu upload URL hết hạn.

## 5. Data layer

Mở rộng `frontend/src/lib/data.ts` hoặc tách feature adapters:

```text
createResidentAssistantConversation()
fetchResidentAssistantConversation(id)
sendResidentAssistantMessage(id, payload)

createManagerAssistantConversation()
fetchManagerAssistantConversation(id)
sendManagerAssistantMessage(id, payload)

fetchAIWorkflow(id)
cancelAIWorkflow(id)
```

Types phải mirror backend response, không dùng `Record<string, unknown>` cho workflow action chính.

Các type tối thiểu:

```ts
type AIWorkflowState =
  | "collecting"
  | "awaiting_confirmation"
  | "executing"
  | "completed"
  | "cancelled"
  | "failed"
  | "awaiting_publish_confirmation"
  | "publishing"
  | "published";

interface AIAction {
  type: string;
  action_id: string;
  requires_confirmation: boolean;
  payload: Record<string, unknown>;
}

interface AIWorkflowResponse {
  workflow_id: string;
  workflow_type: "resident_ticket" | "manager_announcement";
  state: AIWorkflowState;
  workflow_version: number;
  draft: Record<string, unknown>;
  missing_fields: string[];
  action: AIAction | null;
  attachment_ids: string[];
  message: ConversationMessage;
  ticket?: Ticket | null;
  announcement?: Announcement | null;
  citations: Citation[];
}
```

## 6. Query/mutation behavior

- On send success, append/refetch conversation messages and update workflow cache from response.
- On `409`, keep composer draft/attachments, refetch workflow and show “nội dung đã thay đổi”.
- On `422`, map `error.fields` to field/question display.
- On `401`, rely on API client refresh; on failure redirect login.
- On `403`, hide/disable manager assistant for unauthorized role and show permission error.
- On `404`, clear invalid query ID and show unavailable state, never fallback to demo workflow.
- On mutation retry, preserve `action_id`/idempotency key.
- Use `setQueryData` for response object and invalidate conversation/workflow/object detail as necessary.

## 7. SSE integration

SSE client phải parse both event and data. Event-to-cache behavior:

| Event | Frontend action |
| --- | --- |
| `conversation.message.created` | Refetch matching resident/manager assistant conversation. |
| `ticket.created` | Invalidate resident ticket list/detail and relevant workflow. |
| `announcement.updated` | Invalidate manager announcement detail/list and workflow. |
| `announcement.published` | Invalidate resident announcement list/unread count and manager detail. |
| `conversation.handoff.changed` | Refetch resident ticket conversation/management handoff, not manager assistant workflow unless IDs match. |

Không render event content trực tiếp thay cho REST response nếu event chỉ là metadata. Dedupe event bằng message/event ID nếu backend cung cấp.

## 8. Routing and role guards

- `/app/chat`: resident only.
- `/management/assistant`: manager/admin only.
- `/management/conversations/*`: management handoff only, không dùng cho announcement assistant.
- Nếu account role chưa hydrate, hiển thị loading guard; không render manager tool dựa vào demo account.
- Backend vẫn là authority; frontend role guard chỉ là UX.

## 9. UX copy and accessibility

- Hiển thị rõ “Bản nháp ticket” và “Bản nháp announcement”.
- Confirmation action phải có summary, không chỉ nút “Yes”.
- Attachment button có label/tooltip, file list có keyboard access.
- Khi Agent hỏi lại, focus về composer nhưng không xóa draft.
- Khi upload, dùng aria-live cho trạng thái.
- Khi action đang executing, prevent double submit.
- Không hiển thị hướng dẫn kỹ thuật nội bộ như token/version trong UI thường; có thể hiển thị version trong manager advanced detail nếu cần debug.

## 10. Test plan

### Component/unit

- Composer giữ attachments qua nhiều lượt.
- Remove attachment không làm mất text draft.
- Action confirmation gửi đúng action ID/version/idempotency.
- Manager publish confirmation tách khỏi create draft confirmation.
- Scope preview render đúng all/project/building/unit.
- 409 giữ local draft và refetch.

### Integration/browser

Resident:

1. Chọn unit thật.
2. Gửi message thiếu location.
3. Trả lời location.
4. Xem preview.
5. Upload ảnh.
6. Confirm.
7. Mở ticket thật và thấy attachment.
8. Reload conversation.

Manager:

1. Mở `/management/assistant`.
2. Mô tả announcement thiếu scope.
3. Chọn/cung cấp scope.
4. Upload PDF/ảnh.
5. Review preview.
6. Confirm tạo draft.
7. Confirm publish riêng.
8. Resident thuộc audience nhận announcement qua SSE.

Security:

- resident không truy cập manager assistant;
- staff không tạo/publish announcement;
- attachment của actor khác không download/attach được;
- không có demo ID trong Network khi mocks false.

## 11. Deliverables

- Resident assistant chat integration.
- Manager announcement assistant screens.
- Shared attachment uploader/download component.
- Typed API adapters/query hooks.
- SSE cache integration.
- Loading/error/conflict/accessibility states.
- Unit/component/browser tests.
