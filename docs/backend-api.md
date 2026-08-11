# OnBxrd Backend API

## Run locally

PostgreSQL + pgvector:

```powershell
docker compose up --build
```

SQLite fallback without Docker:

```powershell
$env:DATABASE_URL="sqlite+aiosqlite:///./data/app.db"
python -m alembic upgrade head
uvicorn src.main:app --reload --port 8000
```

Swagger UI is available at `http://localhost:8000/docs`.

## Authentication

Authenticated endpoints use `Authorization: Bearer <access-token>`. Access tokens are short-lived JWTs;
refresh tokens are rotated and backed by revocable database sessions.

Before the first startup, configure a unique `JWT_SECRET_KEY` and `MANAGEMENT_BOOTSTRAP_TOKEN`. The first
management administrator is created once through `POST /api/v1/auth/bootstrap-management` with the bootstrap
token in `X-Bootstrap-Token`. Further management accounts must be created by an authenticated administrator.

Resident registration requires a matching active resident profile, using the pre-provisioned `resident_code`
and email. Public callers cannot choose an account role.

The old `X-Actor-*` headers are available only when `DEV_AUTH_ENABLED=true`; they are disabled by default and
rejected by production configuration.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/auth/bootstrap-management` | Create the first management admin once |
| `POST` | `/api/v1/auth/register/resident` | Register against a pre-provisioned resident profile |
| `POST` | `/api/v1/auth/login` | Authenticate with email/password |
| `POST` | `/api/v1/auth/refresh` | Rotate refresh token and issue a new token pair |
| `POST` | `/api/v1/auth/logout` | Revoke one refresh session |
| `POST` | `/api/v1/auth/logout-all` | Revoke all sessions and access tokens |
| `POST` | `/api/v1/auth/change-password` | Change password and revoke all old tokens |
| `POST` | `/api/v1/auth/forgot-password` | Request a reset email without revealing whether an email exists |
| `POST` | `/api/v1/auth/reset-password` | Consume a 15-minute reset token and revoke old sessions/JWTs |
| `GET` | `/api/v1/auth/me` | Get the authenticated account/profile |
| `POST` | `/api/v1/management/accounts` | Admin creates a management account |
| `GET` | `/api/v1/management/accounts` | Admin lists management accounts |
| `PATCH` | `/api/v1/management/accounts/{id}` | Admin changes role/profile/account status |
| `DELETE` | `/api/v1/management/accounts/{id}` | Manager/admin deletes a resident account; admin deletes a management account |
| `GET` | `/api/v1/management/residents` | Management lists/searches resident profiles (`search`, `is_active`, `offset`, `limit`) |
| `GET` | `/api/v1/management/residents/{id}` | Management gets a resident profile, units and account status |
| `PATCH` | `/api/v1/management/residents/{id}` | Manager/admin updates resident profile fields |
| `DELETE` | `/api/v1/management/residents/{id}/account` | Manager/admin deletes only the resident login account |
| `GET` | `/api/v1/management/dashboard` | Operational ticket/resident/knowledge counters |
| `GET` | `/api/v1/management/conversations/handoffs` | Queue of conversations waiting for management reply |
| `POST` | `/api/v1/management/conversations/{id}/takeover` | Explicitly reassign a conversation to the current manager |
| `POST` | `/api/v1/management/conversations/{id}/messages` | Management reply in the existing conversation |
| `POST` | `/api/v1/management/conversations/{id}/handoff-to-bot` | Return an active management conversation to the chatbot |
| `POST` | `/api/v1/management/tickets/{id}/conversation/messages` | Management reply using a ticket id |
| `POST` | `/api/v1/management/tickets/{id}/conversation/takeover` | Explicitly reassign a ticket conversation to the current manager |
| `POST` | `/api/v1/management/tickets/{id}/conversation/handoff-to-bot` | Return a ticket conversation to the chatbot |
| `PATCH` | `/api/v1/management/tickets/{id}/assignment` | Assign/unassign a ticket and due date |
| `POST` | `/api/v1/residents` | Management creates a resident |
| `POST` | `/api/v1/units` | Management creates a unit |
| `POST` | `/api/v1/residents/{id}/units` | Management links a resident to a unit |
| `GET` | `/api/v1/residents/me` | Resident profile and accessible units |
| `GET` | `/api/v1/conversations/{id}` | Conversation detail for its resident or management |
| `POST` | `/api/v1/tickets` | Create a ticket from the normal form flow |
| `GET` | `/api/v1/tickets` | List own tickets or management queue; supports `handoff_status` |
| `GET` | `/api/v1/tickets/{id}` | Ticket detail and audit events |
| `GET` | `/api/v1/tickets/{id}/conversation` | Ticket detail plus its dedicated conversation messages |
| `POST` | `/api/v1/tickets/{id}/messages` | Ask the chatbot or add context inside that ticket conversation |
| `PATCH` | `/api/v1/tickets/{id}/status` | Apply an allowed status transition |
| `POST` | `/api/v1/chat/messages` | General handbook Q&A or chatbot ticket flow; accepts `ticket_id` for ticket context |
| `POST` | `/api/v1/attachments/presign` | Create attachment metadata and a presigned private-S3 PUT URL |
| `GET` | `/api/v1/attachments/{id}/download` | Create a presigned private-S3 GET URL after authorization |
| `GET` | `/api/v1/realtime/stream` | Authenticated SSE stream for conversation/ticket events |
| `POST` | `/api/v1/knowledge/documents` | Upload a handbook/regulation |
| `GET` | `/api/v1/knowledge/documents` | List and filter knowledge documents |
| `PATCH` | `/api/v1/knowledge/documents/{id}/status` | Update indexing state |

Every ticket has exactly one dedicated conversation. Form creation creates the conversation automatically;
chatbot creation binds the confirmed ticket to the conversation that collected the request. Status transitions add
system messages to the same conversation. A conversation can move from `bot_active` to `waiting_management` when
the agent returns a handoff action, then to `management_active` when a manager replies. Resident follow-up messages
remain in the same history and are acknowledged without being sent back to the bot while management owns the handoff.
Management can explicitly return the conversation with `POST /management/conversations/{id}/handoff-to-bot`; this
records a system message, clears the active handoff timestamp, and changes the state back to `bot_active`. The next
resident message then invokes the agent with the complete conversation history.
Opening a conversation is read-only. The first management message atomically assigns `assigned_manager_id` to its
author and moves the conversation to `management_active`; another manager receives `409 Conflict`. Subsequent
management writes should include the `conversation_version` returned by the conversation endpoint or previous write.
The backend updates the owner and version in the same conditional transaction, so a stale tab also receives `409`.
There is no automatic lease or expiry. To recover an abandoned assignment, a manager explicitly calls the `takeover`
endpoint with the current version; the action is audited as a system message. Handback clears the assignment and
returns the conversation to `bot_active`.
Send an `Idempotency-Key` header with form ticket requests. Chat requests use the `idempotency_key` body field because
confirmation is part of the conversation command.

### Attachments and realtime

Attachment upload is deliberately a two-step client flow: call `POST /attachments/presign`, PUT the bytes directly
to the returned S3 URL with the returned MIME type, then include the returned `id` in `attachment_ids` on a ticket
or message request. There is no complete/checksum endpoint in the MVP. The bucket remains private; downloads also
use short-lived presigned URLs. Pending metadata can be linked later to one ticket and/or one conversation message.

`GET /realtime/stream` is an authenticated Server-Sent Events stream. It emits `conversation.message.created`,
`conversation.handoff.changed`, `conversation.assignment.changed`, `ticket.created`, `ticket.status.changed`, and
`ticket.assignment.changed`. REST remains the source for history and CRUD; SSE only pushes committed changes. The
current deployment uses an in-memory single-process connection manager, so a browser should reconnect and reload the
conversation/ticket history after a disconnect. Native `EventSource` clients can pass the short-lived access JWT as
`?access_token=...`; clients using `fetch` streaming can use the normal `Authorization` header.

Password-reset email delivery uses SMTP through FastAPI `BackgroundTasks`. SMTP is optional in local development;
the endpoint always returns the same response for existing and unknown email addresses.

Management roles are `admin`, `manager`, and `staff`. Admins manage management accounts; managers and admins can
delete resident login accounts. Deleting a resident account preserves the resident profile, unit links, tickets,
conversations and history. Only admins can delete management accounts, and the last active admin and the current
admin account cannot be deleted. Managers and admins can assign any active management account; staff can only assign
unassigned tickets to themselves. All management roles can process ticket status transitions and access the
operational dashboard.

## Agent action contract

The backend accepts a structured action from the agent:

```json
{
  "type": "create_ticket",
  "payload": {
    "unit_id": "uuid",
    "category": "plumbing",
    "priority": "high",
    "title": "Water leak",
    "description": "Water is leaking under the kitchen sink.",
    "location": "Unit A-1204, kitchen"
  }
}
```

For an unanswered question, the agent can return:

```json
{
  "type": "handoff_to_management",
  "payload": {"reason": "Requires an operational decision"}
}
```

Management handback accepts an optional note:

```json
{
  "note": "The remaining question is covered by the handbook."
}
```

Without `confirm_action: true`, the backend changes this to `confirm_ticket` and does not persist a ticket. After confirmation, the payload goes through the same `TicketService` used by `POST /tickets`.
