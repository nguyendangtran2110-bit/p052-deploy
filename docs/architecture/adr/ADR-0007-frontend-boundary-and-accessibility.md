# ADR-0007: Role-Specific Responsive Web Client and WCAG 2.2 AA

**Status:** Accepted
**Date:** 2026-08-11

## Context

Resident flows are mobile-first. Manager flows are desktop-first but must remain usable on smaller screens. WCAG 2.2 AA is approved. No frontend project currently exists, while existing architecture notes point to React/Next.js.

## Decision

Use one TypeScript Next.js/React web client with public, resident, manager, and administrator route shells. Support core workflows from 360 CSS px upward with breakpoints at 768, 1024, and 1280 CSS px. Apply WCAG 2.2 AA across both role experiences.

The frontend owns presentation, accessible dialogs, responsive layout, account/epoch-bound unsaved edit buffers, a single-flight draft save queue, and visible field-level conflict recovery. The backend owns the persistent account draft generation/version, identity, authorization, scope, snapshots, state transitions, durable submission results, and notification durability.

## Rationale

- Reuses the repository's intended React/Next.js direction.
- A single web client shares authentication, accessibility, API, and design-system infrastructure.
- Explicit state ownership prevents client-side authorization or duplicated ticket logic.

## Tradeoffs

- Manager tables require alternative compact/card layouts on narrow screens.
- One application bundle contains multiple role shells and requires disciplined code splitting.
- Accessibility acceptance adds design/test work before frontend stories are complete.

## Consequences

Frontend implementation must define loading/empty/error/conflict states per flow, generate or validate API types from OpenAPI, and independently verify WCAG 2.2 AA before release.
