# ADR-0005: Immutable Ticket Snapshots and Optimistic State Transitions

**Status:** Accepted
**Date:** 2026-08-11

## Context

Opening full ticket detail automatically changes `Pending` to `Resolving`. All managers whose current scope covers the ticket may access it, including managers registered after submission. Concurrent manager actions must preserve the first accepted state and notify the losing manager. Resident moves must not rewrite old tickets.

## Decision

- Submission stores immutable resident and building/floor/room snapshots.
- Ticket access for managers compares current grants to the immutable ticket scope.
- Full detail invokes an idempotent open command carrying observed status/version; queue/list reads remain side-effect-free.
- Tickets carry an integer version.
- Terminal mutations require `expected_version` and update by compare-and-swap.
- The first matching `PENDING -> RESOLVING` compare-and-swap wins. A concurrent stale opener returns `ticket_open_conflict` and one notification; a later request that observed current `RESOLVING` is a normal read.
- Terminal mutations use the same first-valid-write-wins rule; stale attempts return `ticket_state_conflict` and one notification.
- There is no responsible-manager field; actor attribution lives in append-only events.

## Rationale

- Preserves historical truth after resident moves.
- Allows new in-scope managers to service old tickets.
- Avoids pessimistic locks held across browser interaction.
- Makes conflict behavior observable and testable.

## Tradeoffs

- Managers may see a conflict after taking an action on stale data.
- Every mutation and client form must carry a version.
- Open attempts require an idempotency key so a winning retry is not misclassified as a loser.
- Scope changes can remove access to a ticket a manager previously handled.

## Consequences

`PENDING -> RESOLVING -> RESOLVED|DENIED` is the only MVP path. `DENIED` requires explanation; `RESOLVED` does not. Terminal confirmation is UX behavior while the backend remains the final validator.
