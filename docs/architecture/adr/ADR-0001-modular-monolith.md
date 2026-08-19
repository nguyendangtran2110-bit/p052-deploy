# ADR-0001: Modular Monolith with Shared Worker Package

**Status:** Accepted
**Date:** 2026-08-11

## Context

The repository already contains one FastAPI/Python backend and an early LangGraph/RAG prototype. The MVP adds identity, scope, onboarding, tickets, notifications, administrator operations, and a new web client. Splitting these immature boundaries into independent services would add distributed transactions and deployment overhead before ownership/load requirements justify them.

## Decision

Use a modular monolith:

- one FastAPI API process;
- explicit identity, scope, onboarding, benefits, tickets, notifications, assistant, and audit modules;
- one worker process built from the same backend package; and
- external providers behind adapters.

Routes call application services. Application services own transactions. Repositories own tables. Modules do not write another module's tables directly.

## Rationale

- Reuses the existing backend conventions.
- Keeps ticket/notification/audit mutations transactional.
- Reduces deployment and operational complexity for the MVP.
- Preserves clear boundaries that can be extracted later if real scaling or ownership pressure appears.

## Tradeoffs

- One deployment can contain more code than a narrowly scoped service.
- Module discipline must be enforced in review because process boundaries do not enforce it.
- Independent scaling is limited until a module is extracted.

## Consequences

No new microservice, message broker, cache cluster, or network boundary is introduced without a later ADR. Database-backed jobs/outbox provide asynchronous behavior for MVP.
