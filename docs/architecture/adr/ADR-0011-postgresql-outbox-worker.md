# ADR-0011: PostgreSQL Outbox with At-Least-Once Workers

**Status:** Accepted
**Date:** 2026-08-11

## Context

Automated onboarding reminders, cleanup, and notification fan-out must survive API restarts without requiring a separate message broker in MVP.

## Decision

Commit outbox/job rows in the same PostgreSQL transaction as source events. Workers atomically lease due rows using `FOR UPDATE SKIP LOCKED` or equivalent, process at least once, and track `not_before`, attempt count, lease owner/expiry, stable error code, and state. Retries use bounded backoff; exhausted jobs move to `dead`. Consumers enforce unique source/recipient idempotency keys.

## Rationale

- Preserves source-event/job consistency within the modular monolith.
- Avoids a new broker while providing crash recovery.
- Makes duplicate delivery behavior explicit.

## Tradeoffs

- PostgreSQL carries queue workload and requires backlog monitoring.
- At-least-once processing requires idempotent consumers.

## Consequences

Operational dashboards expose backlog, lease failures, and dead jobs. Adding a broker later must preserve the same delivery and idempotency contract.
