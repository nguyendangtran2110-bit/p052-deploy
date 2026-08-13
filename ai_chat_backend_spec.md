# AI Chat Backend Specification

## 1. Mục tiêu

Bổ sung backend orchestration, persistence, API và authorization cho AI chat actions theo `ai_chat_actions_spec.md`. Backend phải là nơi kiểm soát workflow state, validation, permission, idempotency và side effect; không giao các trách nhiệm này cho frontend hoặc LLM.

## 2. Nguyên tắc kiến trúc

- Giữ FastAPI monolith hiện tại.
- Tái sử dụng `ChatService`, `TicketService`, `AnnouncementService`, `AttachmentService`, conversation/realtime services.
- Không cho Agent tự thao tác SQL.
- Không clone toàn bộ Ticket service cho Announcement workflow.
- Tách manager assistant conversation khỏi resident handoff conversation về `workflow_type`, dù có thể tái sử dụng bảng `conversations`.
- Migration phải qua Alembic.
- Các write action phải transactionally persist workflow/action result và domain object khi có thể.

## 3. Database design

### 3.1. Mở rộng `conversations`

Thêm các field sau nếu dùng conversation chung cho cả hai assistant:

```text
conversation_type
workflow_type
workflow_id nullable
```

Allowed values:

```text
conversation_type: resident_support | manager_assistant
workflow_type: resident_ticket | manager_announcement | null
```

Backward compatibility:

- Conversation ticket hiện tại giữ `conversation_type=resident_support`.
- Conversation general resident cũng giữ `resident_support`.
- Conversation handoff resident-manager không được gán `manager_assistant`.

### 3.2. Bảng `ai_workflows`

```text
id UUID primary key
conversation_id UUID not null references conversations(id)
workflow_type varchar not null
owner_actor_id varchar not null
owner_resident_id UUID nullable
state varchar not null
version integer not null default 0
draft JSON not null default {}
missing_fields JSON not null default []
pending_action JSON nullable
attachment_ids JSON not null default []
result JSON nullable
last_error JSON nullable
created_at timestamp not null
updated_at timestamp not null
completed_at timestamp nullable
```

Constraints/indexes:

- `workflow_type` in `resident_ticket`, `manager_announcement`.
- `state` in shared state machine values.
- Index `(conversation_id, updated_at)`.
- Index `(owner_actor_id, state)`.
- At most one active workflow of the same type per conversation unless explicit restart is implemented.

Không lưu binary hoặc presigned URL trong `draft`/`result`.

### 3.3. Bảng `ai_workflow_actions`

```text
id UUID primary key
workflow_id UUID not null references ai_workflows(id)
action_id varchar not null
action_type varchar not null
workflow_version integer not null
status varchar not null
request_payload JSON not null
response_payload JSON nullable
error_payload JSON nullable
created_at timestamp not null
completed_at timestamp nullable
```

Unique constraint:

```text
UNIQUE(workflow_id, action_id)
```

Allowed status:

```text
pending, executing, succeeded, failed, unknown, cancelled
```

Bảng này là idempotency ledger cho Agent actions. `request_payload` phải redact dữ liệu nhạy cảm nếu cần.

### 3.4. Attachment ownership

Tái sử dụng `ticket_attachments` hiện tại. Không đổi tên trong MVP. Bổ sung logic để attachment orphan có thể liên kết với workflow trước khi domain object tồn tại:

```text
workflow_id UUID nullable references ai_workflows(id)
```

Hoặc, nếu không muốn migration thêm cột, lưu IDs trong `ai_workflows.attachment_ids` và chỉ cho phép attachment do actor hiện tại upload. Chọn một phương án và bảo đảm query authorize được.

Khuyến nghị thêm `workflow_id` để kiểm tra ownership rõ ràng và tránh attachment ID bị chuyển giữa workflow.

## 4. API contract

### 4.1. Resident assistant

Có thể mở rộng endpoint hiện tại:

```http
POST /api/v1/chat/messages
```

Request mở rộng:

```json
{
  "message": "Máy lạnh phòng ngủ bị chảy nước",
  "conversation_id": "uuid|null",
  "workflow_id": "uuid|null",
  "workflow_version": 3,
  "unit_id": "uuid",
  "attachment_ids": ["uuid"],
  "confirmed_action_id": "uuid|null",
  "confirm_action": false,
  "idempotency_key": "uuid|null"
}
```

Backward compatibility: các request cũ không có workflow fields vẫn được xử lý, nhưng side-effect action mới phải đi qua workflow validation.

### 4.2. Manager assistant

Tạo endpoint riêng để tránh trộn manager assistant với resident handoff:

```http
POST /api/v1/management/assistant/conversations
POST /api/v1/management/assistant/conversations/{conversation_id}/messages
GET  /api/v1/management/assistant/conversations/{conversation_id}
```

Request message:

```json
{
  "message": "Soạn thông báo bảo trì thang máy tòa A vào ngày mai",
  "workflow_id": "uuid|null",
  "workflow_version": 2,
  "attachment_ids": ["uuid"],
  "confirmed_action_id": "uuid|null",
  "confirm_action": false,
  "idempotency_key": "uuid|null"
}
```

All routes require JWT management actor. `staff` không được gọi announcement action vì service hiện chỉ cho manager/admin.

### 4.3. Workflow read/retry/cancel

```http
GET  /api/v1/ai/workflows/{workflow_id}
POST /api/v1/ai/workflows/{workflow_id}/cancel
POST /api/v1/ai/workflows/{workflow_id}/retry
```

MVP có thể không public retry endpoint nếu application tự xử lý retry, nhưng workflow read/cancel cần có để refresh/recover UI. Mọi endpoint phải authorize owner hoặc management admin theo workflow type.

### 4.4. Response chung

```json
{
  "conversation_id": "uuid",
  "workflow_id": "uuid",
  "workflow_type": "resident_ticket",
  "state": "awaiting_confirmation",
  "workflow_version": 3,
  "message": {
    "id": "uuid",
    "role": "assistant",
    "content": "Thông tin đã đủ. Bạn có muốn tạo ticket không?",
    "action_payload": {
      "type": "create_ticket",
      "action_id": "uuid",
      "requires_confirmation": true,
      "payload": {}
    },
    "attachment_ids": [],
    "created_at": "datetime"
  },
  "draft": {},
  "missing_fields": [],
  "action": {},
  "citations": [],
  "ticket": null,
  "announcement": null
}
```

Có thể giữ `ChatMessageResponse` cũ cho compatibility, nhưng frontend mới phải dùng response có workflow fields.

## 5. Application services

### 5.1. `AIWorkflowService`

Tạo module:

```text
src/backend/application/ai_workflows/
    contracts.py
    service.py
    repository.py hoặc dùng infrastructure repository
```

Responsibilities:

- create/get active workflow;
- verify conversation/actor ownership;
- merge draft từ Agent result;
- increment optimistic version;
- persist missing fields/pending action;
- validate confirmation/action ID/version;
- create action ledger record;
- execute/reconcile idempotent action;
- transition workflow state;
- attach workflow attachments;
- map domain result thành API response.

### 5.2. Ticket action

`AIWorkflowService` gọi:

```python
TicketService.create(
    CreateTicketCommand(
        source=TicketSource.CHAT,
        conversation_id=workflow.conversation_id,
        idempotency_key=action_id_or_request_key,
        attachment_ids=workflow.attachment_ids,
        ...,
    ),
    actor,
)
```

Trước khi gọi:

- actor là resident;
- actor sở hữu conversation/workflow;
- unit là active unit của resident;
- required fields đầy đủ;
- action ID chưa succeeded;
- version đúng.

Sau khi thành công:

- lưu result ticket ID/code;
- state `completed`;
- tăng workflow version;
- publish `ticket.created` và `conversation.message.created`;
- trả canonical ticket.

### 5.3. Announcement actions

`create_announcement_draft` gọi `AnnouncementService.create()` với actor manager/admin.

`publish_announcement` gọi `AnnouncementService.publish(announcement_id, version, actor)`.

Không copy logic audience/version vào AI service. `AnnouncementService` vẫn là authority.

Sau publish:

- state `published`;
- lưu announcement ID/version;
- publish `announcement.published` với resident audience IDs theo realtime service;
- không gửi content trong SSE payload.

## 6. Agent runtime integration

Mở rộng protocol hiện tại:

```python
class AgentRuntime(Protocol):
    async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]: ...
```

Giữ protocol đơn giản để test inject fake Agent. Application service phải truyền đầy đủ:

- actor context tối thiểu;
- current conversation messages;
- persisted workflow draft/state;
- selected unit;
- attachment IDs;
- pending action/confirmation;
- handbook context nếu intent Q&A.

Agent result phải validate bằng Pydantic trước khi service dùng.

## 7. Attachment API/authorization

Giữ endpoint:

```http
POST /api/v1/attachments/presign
GET  /api/v1/attachments/{attachment_id}/download
```

Bổ sung workflow ownership:

- Presign có thể nhận `workflow_id`.
- Nếu có `workflow_id`, backend kiểm tra actor sở hữu workflow và workflow type phù hợp.
- Nếu chưa có workflow, attachment gắn actor tạm thời và được bind khi message/workflow tạo.
- Khi tool action chạy, mọi attachment ID phải là attachment của workflow hoặc attachment do actor upload trong cùng conversation.
- Không attach attachment đã thuộc ticket/announcement/message khác.
- Manager announcement attachment chỉ được attach khi announcement draft còn `draft`.

## 8. Conversation và message persistence

- User message được lưu trước khi Agent chạy để retry vẫn có context.
- Assistant message lưu `action_payload`, citations, workflow ID/state/version.
- Message attachment IDs phải được load cùng conversation detail.
- Manager assistant message role có thể là `user`/`assistant`; không dùng `management` cho assistant chat nếu role đó đang mang nghĩa manager reply cho resident.
- Resident handoff message tiếp tục dùng role hiện tại và không được gọi manager announcement Agent.

## 9. Concurrency và idempotency

### Workflow version

Mọi update dùng conditional update:

```sql
UPDATE ai_workflows
SET draft = :draft,
    state = :state,
    version = version + 1
WHERE id = :workflow_id AND version = :expected_version
```

Nếu rowcount là 0, trả `409`.

### Action idempotency

Trước khi execute:

1. Lock/read action ledger.
2. Nếu `succeeded`, trả lại response đã lưu.
3. Nếu `pending/executing`, không tạo side effect lần hai; reconcile theo object/action key.
4. Nếu `failed`, chỉ retry khi policy cho phép.

Ticket hiện có unique `(resident_id, idempotency_key)`. Dùng action ID ổn định để map vào key. Announcement cần action ledger vì bảng announcement chưa có idempotency key.

## 10. RBAC và business validation

- Resident chỉ được tạo ticket cho resident/unit của mình.
- Manager/admin mới được tạo/publish announcement.
- Staff không được dùng announcement tools.
- Admin có thể publish/archive theo AnnouncementService.
- Pydantic validate UUID/enum/length.
- Domain service validate active unit, audience scope, status transition, expiry và attachment parent.
- Không dùng `X-Actor-*` trong production; test/dev auth chỉ dùng test.

## 11. Realtime

Sau domain commit mới publish event:

- `conversation.message.created`: resident/manager assistant conversation phù hợp.
- `ticket.created`: resident và management.
- `announcement.updated`: management.
- `announcement.published`: audience residents + management.

SSE payload tối thiểu:

```json
{
  "event": "ticket.created",
  "ticket_id": "uuid",
  "conversation_id": "uuid",
  "ticket_code": "TKT-..."
}
```

Không publish trước commit. Nếu một event không đến được in-memory subscriber, REST reload vẫn là source of truth.

## 12. API errors

Map exception hiện tại:

- `AuthenticationError` -> 401
- `AuthorizationError` -> 403
- `NotFoundError` -> 404
- `ConflictError` -> 409
- `ValidationError` -> 422

Workflow response khi Agent thiếu field là response nghiệp vụ thành công, không phải HTTP 422.

## 13. Migration và compatibility

- Tạo Alembic migration cho workflow/action tables và conversation/attachment columns nếu chọn.
- Migration phải chạy được trên SQLite test và PostgreSQL production.
- Backfill conversation cũ thành `resident_support`.
- Không bắt buộc backfill workflow cho conversation cũ; tạo workflow khi user bắt đầu action mới.
- API cũ `/chat` và `/chat/messages` tiếp tục hoạt động cho handbook/ticket compatibility.
- Manager assistant endpoint mới không được làm thay đổi semantics `/management/conversations/{id}/messages`.

## 14. Backend tests

### Unit

- workflow transitions;
- required field validation;
- draft merge;
- stale version conflict;
- action ledger idempotency;
- attachment ownership;
- RBAC.

### API integration

1. Resident first message creates workflow and asks missing field.
2. Multiple messages merge draft.
3. Confirm creates one ticket with correct source/conversation/attachments.
4. Duplicate confirmation returns same ticket.
5. Manager creates announcement draft via assistant.
6. Draft confirmation does not publish.
7. Separate publish confirmation publishes exact version.
8. Manager outside ownership/admin rules receives 403.
9. Stale workflow version receives 409 without side effect.
10. Attachment permissions and S3 presign/download work for ticket/announcement.
11. SSE events emitted only after commit and with minimal payload.

## 15. Deliverables

- Alembic migration.
- Workflow/action schemas and services.
- Resident assistant API integration.
- Manager assistant API.
- Attachment workflow binding.
- Realtime events.
- OpenAPI schemas/examples.
- Backend tests and migration verification on SQLite/PostgreSQL.
