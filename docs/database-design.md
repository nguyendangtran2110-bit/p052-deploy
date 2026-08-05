# OnBxrd Backend Database Design

## Pham vi

Co so du lieu phuc vu bon nhom nghiep vu: tai khoan/xac thuc, cu dan/can ho, hoi thoai/ticket, va kho tri thuc tu handbook/regulation. Backend la source of truth; agent khong ghi truc tiep vao database.

## Entity relationship

```mermaid
erDiagram
    RESIDENTS o|--o| USER_ACCOUNTS : authenticates
    USER_ACCOUNTS ||--o| MANAGEMENT_PROFILES : describes
    USER_ACCOUNTS ||--o{ REFRESH_SESSIONS : owns
    USER_ACCOUNTS o|--o{ TICKETS : assigned
    RESIDENTS ||--o{ RESIDENT_UNITS : occupies
    UNITS ||--o{ RESIDENT_UNITS : has
    RESIDENTS ||--o{ CONVERSATIONS : starts
    UNITS ||--o{ CONVERSATIONS : scopes
    CONVERSATIONS ||--o{ MESSAGES : contains
    RESIDENTS ||--o{ TICKETS : creates
    UNITS ||--o{ TICKETS : concerns
    CONVERSATIONS o|--o{ TICKETS : originates
    TICKETS ||--o{ TICKET_EVENTS : audits
    TICKETS ||--o{ TICKET_ATTACHMENTS : includes
    KNOWLEDGE_DOCUMENTS ||--o{ KNOWLEDGE_CHUNKS : splits
```

## Bang du lieu

| Bang | Muc dich | Rang buoc quan trong |
|---|---|---|
| `user_accounts` | Danh tinh dang nhap cho cu dan va ban quan ly | Email unique, role/status check, token version de revoke access token |
| `management_profiles` | Ho so nhan vien ban quan ly | Employee code unique, role `admin/manager/staff` |
| `refresh_sessions` | Phien refresh token co the thu hoi | Chi luu SHA-256 cua token, expiry, revoke va replacement chain |
| `residents` | Ho so cu dan | `resident_code`, email va phone unique |
| `units` | Can ho trong du an/toa nha | Unique theo project + building + unit number |
| `resident_units` | Quan he nhieu-nhieu cu dan/can ho | Backend dung bang nay de kiem tra quyen tao ticket |
| `conversations` | Phien chat, co the anonymous khi chi hoi handbook | Gan resident/unit khi da xac thuc |
| `messages` | Lich su user/assistant, citation va structured action | Khong luu chain-of-thought/internal analysis |
| `tickets` | Yeu cau tu form hoac chatbot | Unique `(resident_id, idempotency_key)`, assignee va due date |
| `ticket_events` | Audit log bat bien cua ticket | Luu actor, trang thai cu/moi va comment |
| `ticket_attachments` | Metadata file dinh kem | File duoc luu qua storage adapter |
| `knowledge_documents` | Metadata handbook/regulation | SHA-256 unique, co version va pham vi toa nha |
| `knowledge_chunks` | Doan van ban cho retrieval | Unique `(document_id, chunk_index)`, embedding dung pgvector |

## Ticket state machine

```mermaid
stateDiagram-v2
    [*] --> submitted
    submitted --> approved
    submitted --> rejected
    submitted --> cancelled
    approved --> in_progress
    approved --> cancelled
    in_progress --> resolved
    in_progress --> cancelled
```

- Ca form va chatbot deu tao ticket o trang thai `submitted` qua cung `TicketService`.
- Quan ly thuc hien `approved`, `rejected`, `in_progress` va `resolved`.
- Cu dan chi co the huy ticket cua chinh minh khi ticket con `submitted`.
- Moi transition tao mot dong `ticket_events`.

## Hai luong tao ticket

```text
Resident form -> POST /api/v1/tickets -> TicketService -> tickets + ticket_events

Resident chat -> POST /api/v1/chat/messages -> Agent structured action
              -> resident confirms -> TicketService -> tickets + ticket_events
```

Agent chi tra `confirm_ticket/create_ticket` voi payload co cau truc. Backend van kiem tra resident-unit, required fields, transition va idempotency truoc khi persist.

## Local runtime

- PostgreSQL 16 + pgvector la database chinh trong `docker-compose.yml`.
- SQLite + JSON vector fallback chi dung cho test nhanh va local fallback.
- `AUTO_CREATE_TABLES=true` ho tro bootstrap local; Alembic la co che migration chinh.
- File handbook duoc luu trong `KNOWLEDGE_STORAGE_DIR`; database chi luu metadata, checksum va chunks.

## Authentication boundary

- Mat khau duoc hash bang Argon2; database khong luu mat khau ro.
- Access JWT kiem tra chu ky HS256, issuer, audience, expiry, token type va token version.
- Refresh JWT duoc rotate moi lan su dung; database chi luu hash token. Tai su dung token cu se revoke ca token family.
- Doi mat khau, logout-all, khoa tai khoan va doi management role deu tang `token_version` de vo hieu hoa access token cu.
- Cu dan chi dang ky khi `resident_code + email` khop ho so active da duoc ban quan ly tao.
- Bootstrap token chi tao duoc management admin dau tien. Cac tai khoan tiep theo do admin tao.
- Header `X-Actor-*` chi la adapter test khi `DEV_AUTH_ENABLED=true` va bi tat mac dinh.
