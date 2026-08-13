# ADR-0004: Single Persistent Account Ticket Draft

**Status:** Accepted
**Date:** 2026-08-11

## Revision Note

This ADR previously selected a session-only browser workspace. The authoritative MVP requirement changed to a single persistent draft slot shared by an authenticated resident account across sessions and devices, so the decision and filename were revised while retaining stable ADR ID `0004`.

## Context

Residents can begin ticket creation manually or through the assistant and must continue the same draft across routes, logout/login, browsers, and devices. The product permits zero or one active draft per authenticated resident account and requires safe behavior when multiple sessions edit it or an old draft is consumed and a new one begins.

## Decision

Store zero or one active `ticket_draft` row in PostgreSQL, uniquely keyed by the authenticated resident account. It contains an immutable unpredictable `draft_id` for that draft generation, subject, content, urgency, integer version, timestamps, and no editable resident/location fields. Manual form and assistant proposals update the same row.

Draft mutations require `draft_id`, `expected_version`, and an idempotency key. The first valid compare-and-swap on account/generation/version wins; stale sessions receive a generation-aware conflict and must reconcile visibly. Starting a new flow returns the existing draft; UX defaults to resume and requires confirmation to atomically replace it with a new generation. Submission creates the ticket, durable account/key-to-ticket result, and active-draft deletion in one transaction. Same-key retries return the committed ticket; no separate processing-status protocol is used. Logout, refresh, and account session/device changes do not delete the draft.

Active drafts do not expire for inactivity in MVP. Deactivation makes a draft inaccessible without deleting it; restoration exposes the same saved draft. Permanent account deletion and cleanup are outside MVP.

Resident name, phone, building, floor, and room are never stored as editable workspace fields. The backend reads the authenticated resident profile at submission and creates immutable snapshots.

## Rationale

- Meets cross-session and cross-device continuity with one authoritative copy.
- A unique account key prevents multiple active drafts.
- Optimistic concurrency avoids holding locks across user interaction.
- Generation identity prevents stale requests for a deleted/replaced draft from matching a later draft whose version restarted.
- Same-key POST retry plus a durable submission result keeps ambiguous outcomes safe without a second transaction or lease protocol.
- Keeps verified profile data out of model extraction and client authority.

## Tradeoffs

- Draft content becomes persistent sensitive product data and requires database access controls and backup handling.
- Concurrent sessions can receive visible conflicts and must refresh/reapply changes.
- Autosave requires network availability; unsent keystrokes that never reached the API are not durable.

## Consequences

There is one production draft table and an authenticated resident draft API. Anonymous users have no persistent drafts. Administrators and managers receive no draft-content access by default. Existing prototype draft tables are not migrated; the new schema is created through PostgreSQL migrations.
