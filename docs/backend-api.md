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

## Development identity headers

| Actor | Headers |
|---|---|
| Resident | `X-Actor-Role: resident`, `X-Resident-Id: <uuid>` |
| Management | `X-Actor-Role: management`, `X-Actor-Id: <external-id>` |
| Anonymous handbook Q&A | No identity header |

These headers are a local adapter. Replace the dependency that creates `ActorContext` with JWT/OIDC validation before production.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
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

