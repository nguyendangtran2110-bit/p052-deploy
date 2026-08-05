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
| `GET` | `/api/v1/auth/me` | Get the authenticated account/profile |
| `POST` | `/api/v1/management/accounts` | Admin creates a management account |
| `GET` | `/api/v1/management/accounts` | Admin lists management accounts |
| `PATCH` | `/api/v1/management/accounts/{id}` | Admin changes role/profile/account status |
| `GET` | `/api/v1/management/dashboard` | Operational ticket/resident/knowledge counters |
| `PATCH` | `/api/v1/management/tickets/{id}/assignment` | Assign/unassign a ticket and due date |
| `POST` | `/api/v1/residents` | Management creates a resident |
| `POST` | `/api/v1/units` | Management creates a unit |
| `POST` | `/api/v1/residents/{id}/units` | Management links a resident to a unit |
| `GET` | `/api/v1/residents/me` | Resident profile and accessible units |
| `POST` | `/api/v1/tickets` | Create a ticket from the normal form flow |
| `GET` | `/api/v1/tickets` | List own tickets or management queue |
| `GET` | `/api/v1/tickets/{id}` | Ticket detail and audit events |
| `PATCH` | `/api/v1/tickets/{id}/status` | Apply an allowed status transition |
| `POST` | `/api/v1/chat/messages` | Handbook Q&A or chatbot ticket flow |
| `POST` | `/api/v1/knowledge/documents` | Upload a handbook/regulation |
| `GET` | `/api/v1/knowledge/documents` | List and filter knowledge documents |
| `PATCH` | `/api/v1/knowledge/documents/{id}/status` | Update indexing state |

Send an `Idempotency-Key` header with form ticket requests. Chat requests use the `idempotency_key` body field because confirmation is part of the conversation command.

Management roles are `admin`, `manager`, and `staff`. Admins manage accounts; managers and admins can assign
any active management account; staff can only claim unassigned tickets for themselves. All management roles can
process ticket status transitions and access the operational dashboard.

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

Without `confirm_action: true`, the backend changes this to `confirm_ticket` and does not persist a ticket. After confirmation, the payload goes through the same `TicketService` used by `POST /tickets`.
