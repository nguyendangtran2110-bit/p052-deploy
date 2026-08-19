# ADR-0009: Durable Notification Campaigns with Preview Revalidation

**Status:** Accepted
**Date:** 2026-08-11

## Context

Managers target buildings, floors, units, or residents, and ticket detail provides a resident-preselected `Notify` action. Scope or resident membership can change between preview and send, and retries must not duplicate notifications.

## Decision

Persist a manager-authored campaign intent with subject/content, normalized selector, scope version, preview recipient hash/count, exact accepted recipient snapshot, and idempotency key. Whole-building targeting requires that building's `ALL_FLOORS` grant. Send refreshes scope and re-resolves recipients; any difference returns `notification_preview_stale` without sending.

Ticket `Notify` opens a composer and server-derived resident preview, then uses the same explicit campaign send contract. Worker fan-out creates one recipient notification per campaign/account using a unique key.

## Rationale

- Makes authorization and user intent auditable.
- Prevents a preview from silently expanding.
- Provides one contract for ticket contact and general manager notices.

## Tradeoffs

- Requires preview persistence and a second request before send.
- Large audiences are accepted asynchronously rather than created inline.

## Consequences

There is no immediate-send `/notify` endpoint. Notification type catalog and retention remain deferred.
