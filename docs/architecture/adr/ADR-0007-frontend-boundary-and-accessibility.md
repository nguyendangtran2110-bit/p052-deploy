# ADR-0007: Role-Specific Desktop-First Web Client and WCAG 2.2 AA

**Status:** Accepted
**Date:** 2026-08-11

## Context

Resident and manager flows are desktop-first. Mobile and tablet UX/UI are outside MVP scope. WCAG 2.2 AA remains approved, including zoom and reflow behavior required for desktop accessibility. No frontend project currently exists, while existing architecture notes point to React/Next.js.

## Decision

Use one TypeScript Next.js/React web client with public, resident, manager, and administrator route shells. Design resident and manager workflows desktop-first, with a minimum product-supported viewport of 1024 CSS px at 100% browser zoom and layout targets at 1024, 1280, and 1440 CSS px and above. Do not require mobile or tablet-specific shells, navigation, compact data representations, or acceptance tests below 1024 CSS px at 100% zoom. Apply WCAG 2.2 AA across both role experiences, including 200% zoom and 400%/320 CSS px equivalent reflow on desktop.

The frontend owns presentation, accessible dialogs, desktop layout, account/epoch-bound unsaved edit buffers, a single-flight draft save queue, and visible field-level conflict recovery. The backend owns the persistent account draft generation/version, identity, authorization, scope, snapshots, state transitions, durable submission results, and notification durability.

## Rationale

- Reuses the repository's intended React/Next.js direction.
- A single web client shares authentication, accessibility, API, and design-system infrastructure.
- Explicit state ownership prevents client-side authorization or duplicated ticket logic.

## Tradeoffs

- Phone- and tablet-specific access patterns are intentionally unspecified; any future mobile or tablet work requires separate scope approval.
- One application bundle contains multiple role shells and requires disciplined code splitting.
- Accessibility acceptance adds design/test work before frontend stories are complete.

## Consequences

Frontend implementation must define loading/empty/error/conflict states per flow, generate or validate API types from OpenAPI, and independently verify WCAG 2.2 AA before release.
