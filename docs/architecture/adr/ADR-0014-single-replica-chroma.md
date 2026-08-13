# ADR-0014: Single-Replica Read-Only Chroma Runtime

**Status:** Accepted
**Date:** 2026-08-11

## Context

The brownfield assistant uses a locally persisted Chroma index. Shared-write and horizontal-runtime behavior are not established, and performance targets are explicitly deferred.

## Decision

Retain Chroma for MVP as a versioned index mounted read-only by one assistant-serving API replica. Build and validate a new index outside runtime, then switch versions during an explicit maintenance window. PostgreSQL remains the product source of truth, and assistant degradation never blocks manual ticket or other core flows.

## Rationale

- Reuses the working knowledge prototype without inventing a distributed vector service.
- Avoids concurrent index writers and unclear persistence semantics.
- Keeps the index reproducible and replaceable.

## Tradeoffs

- Assistant serving is single-replica and may pause during index replacement.
- Horizontal assistant scaling requires a later architecture decision.

## Consequences

Deployment health distinguishes assistant dependency degradation from core API readiness. Quantitative scale/performance decisions remain deferred.
