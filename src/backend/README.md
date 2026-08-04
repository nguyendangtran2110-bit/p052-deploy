# Backend Package Structure

The backend is a modular monolith organized by layer and business feature.

```text
backend/
|-- api/
|   `-- routes/                 # HTTP transport; one file per small feature
|-- application/
|   |-- chat/                   # Chat orchestration and agent contract
|   |-- knowledge/              # Handbook upload/indexing use cases
|   |-- residents/              # Resident and unit use cases
|   `-- tickets/                # Ticket commands and workflow
|-- core/                       # Configuration and technical cross-cutting code
|-- domain/
|   |-- common/                 # Actor context and shared domain errors
|   |-- conversations/
|   |-- identity/
|   |-- knowledge/
|   |-- residents/
|   `-- tickets/
|-- infrastructure/
|   `-- db/
|       |-- models/             # SQLAlchemy models grouped by domain
|       `-- repositories/       # Persistence queries grouped by domain
`-- schemas/
    |-- chat/
    |-- knowledge/
    |-- residents/
    `-- tickets/                # Each feature separates requests/responses
```

## Dependency direction

```text
api -> application -> domain
              `----> infrastructure adapters
```

- API routes validate transport data and call application services.
- Application services own use-case orchestration and transaction boundaries.
- Domain packages contain business vocabulary, policies and errors without FastAPI dependencies.
- Infrastructure contains SQLAlchemy, storage and future JWT/vector adapters.
- Schemas are HTTP contracts, not database models.

## Growth rules

- Add a feature folder when a domain has several independent use cases or more than one substantial file.
- Split use cases into files such as `create_ticket.py` and `transition_ticket.py`; do not create folders named `add`, `edit` or `delete`.
- Keep `core` small and free of business rules.
- Compatibility modules such as `application/ticket_service.py` only re-export symbols for older imports. New code must import from the feature package.

