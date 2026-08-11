# ADR-0012: Exact Manager Scope with Bounded Registry Freshness

**Status:** Accepted
**Date:** 2026-08-11

## Context

Managers may cover exact floors or all floors in selected buildings. Registry maintenance ownership is deferred, but stale authorization cannot remain effective indefinitely.

## Decision

Represent grants as exact `(building_id, floor_id)` pairs or per-building `(building_id, ALL_FLOORS)`. Refresh the registry projection at login, session renewal, and before every scoped mutation. Scope-sensitive reads may use a projection checked within 15 minutes; after that, refresh or fail closed. A changed projection is replaced transactionally, increments `scope_version`, is audited, and invalidates stale protected client/session state.

## Rationale

- Prevents building/floor cross-product authorization.
- Bounds revoked-scope exposure without requiring a registry event feed.
- Centralizes refresh behavior for all modules.

## Tradeoffs

- Registry outages can temporarily block scoped manager work.
- Mutations incur a registry version/freshness check.

## Consequences

Whole-building notifications require `ALL_FLOORS`. New grants expose matching historical tickets; removed grants immediately remove access after refresh. Registry authoring/staffing workflow remains deferred.
