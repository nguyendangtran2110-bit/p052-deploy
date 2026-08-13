# OnBxrd MVP Architecture Diagram

This compatibility diagram points to the authoritative architecture views. The detailed container view is in [`container-architecture.md`](container-architecture.md); trust boundaries are in [`system-context.md`](system-context.md).

```mermaid
flowchart LR
    resident[Resident browser]
    manager[Manager browser]
    admin[Administrator browser]
    edge[Same-origin HTTPS edge]
    web[Next.js web client]
    api[FastAPI modular monolith]
    worker[Background worker]
    db[(PostgreSQL)]
    draft[Zero or one active draft per resident account]
    rag[LangGraph + knowledge adapter]
    chroma[(Chroma MVP index)]
    registry[Resident/manager registry]
    otp[OTP provider]
    zalo[Zalo profile URL]

    resident --> edge
    manager --> edge
    admin --> edge
    edge --> web
    edge -->|/api/*| api
    api --> db
    api --> draft
    draft --> db
    api --> rag
    rag --> chroma
    api --> registry
    api --> otp
    api -. returns validated URL .-> web
    web -. opens profile .-> zalo
    worker --> db
```

The browser is untrusted. Web assets and `/api/*` share one public origin, while FastAPI remains the application boundary. PostgreSQL is the source of truth. The registry is a read/version dependency; OnBxrd owns local account claims. Zalo is an outbound URL handoff only.
