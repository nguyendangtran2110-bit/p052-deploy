# ADR-0002: PostgreSQL as Product Source of Truth

**Status:** Accepted
**Date:** 2026-08-11

## Context

The prototype creates SQLite tables at runtime and also uses Chroma for knowledge retrieval. The approved product requires atomic identity claims, zero or one active draft per resident account, exact scope joins, immutable ticket snapshots, optimistic concurrency, durable notifications, and audit history.

## Decision

Use PostgreSQL as the authoritative store for product data and Alembic for migrations. Chroma remains a replaceable knowledge index only. SQLite is not a production target.

## Rationale

- Relational constraints naturally protect unique identity claims and building-floor scope pairs.
- Transactions support ticket event, status, outbox, and notification consistency.
- Row-version updates implement first-valid-write-wins behavior.
- The repository already anticipates PostgreSQL/Alembic in its dependencies and configuration.

## Tradeoffs

- Local development requires a database service or test container.
- Schema migration discipline becomes mandatory.
- Chroma and PostgreSQL require separate operational handling while the existing RAG implementation is retained.

## Consequences

Runtime table creation in `src/services/mvp.py` is retired. Deployments apply migrations before traffic. No domain may treat browser storage, Chroma, or provider state as authoritative product data.
