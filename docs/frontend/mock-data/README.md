# Frontend Mock API and Data Strategy

This directory documents the frontend-first mock contract. It should contain only synthetic scenarios and fixtures derived from the authoritative API/OpenAPI contract.

## Goals

- Let frontend stories run before every backend endpoint is integrated.
- Exercise loading, empty, failure, conflict, retry, session, scope, and responsive states deterministically.
- Keep mock and integrated builds on the same relative `/api/v1` request paths.
- Detect frontend drift from the backend contract early.

## Authority

1. [`../../architecture/api-contracts.md`](../../architecture/api-contracts.md)
2. Generated or validated backend OpenAPI schemas
3. [`../FRONTEND-SPEC.md`](../FRONTEND-SPEC.md) for frontend state behavior
4. Mock fixtures in this directory

Mock fixtures must not become an independent backend schema source.

## Tooling Boundary

The Developer may use MSW or an equivalent HTTP-boundary mocking tool. The selected tool must:

- Intercept the same relative URLs used in integration.
- Support request bodies, cookies/credentials behavior simulation, CSRF checks, headers, delays, and stable error responses.
- Support deterministic scenario selection in component tests and browser end-to-end tests.
- Avoid importing mock handlers into production bundles.

## Data Safety

- Use obviously synthetic Vietnamese names, buildings, rooms, contacts, tickets, and notifications.
- Do not copy real resident IDs, phone numbers, email addresses, Zalo URLs, credentials, tokens, or production payloads.
- Never place passwords, OTP values used outside local test scenarios, session cookies, provider secrets, or CSRF secrets in committed fixtures.
- Ticket and notification content should be realistic enough to test wrapping, overflow, and Vietnamese diacritics without containing real reports.
- Raw mock request logging must redact password, OTP, contact, draft, ticket, and notification content in the same way expected from production diagnostics.

## Fixture Shape Rules

- IDs are opaque stable test values, not display-derived authorization values.
- Timestamps are UTC ISO 8601 strings.
- Collection fixtures use `{ "items": [], "next_cursor": null }` and exercise cursor pagination.
- Every draft representation includes `draft_id`, `version`, `field_fingerprint`, and `updated_at` as required by the contract.
- Manager ticket rows include only privacy-safe list fields.
- Full Manager ticket detail includes contact snapshot data only in the full-detail fixture.
- Zalo URL values appear only in the scoped Zalo success response, not Manager list/detail fixtures.
- Notification previews contain summary/count/hash/token data and never a bulk contact list.

## Required Scenario Catalog

Suggested scenario identifiers are stable test labels, not product API fields.

### Authentication

| Scenario | Result |
|---|---|
| `auth.login.resident_success` | Resident principal, profile summary, session epoch |
| `auth.login.manager_success` | Manager principal, display scope, scope version |
| `auth.login.invalid` | Generic invalid-credentials response |
| `auth.login.rate_limited` | `429 rate_limited` with retry guidance |
| `auth.session.expired` | `401 authentication_required` |
| `auth.registration.otp_sent` | Challenge, selected channel, masked destination, expiry |
| `auth.registration.identity_claimed` | `409 identity_already_claimed` |
| `auth.registration.otp_invalid` | `422 otp_invalid` |
| `auth.registration.otp_expired` | `422 otp_expired` |
| `auth.registration.attempts_exhausted` | `423 otp_attempts_exhausted` |
| `auth.registration.provider_unavailable` | `502 dependency_unavailable` |

### Resident onboarding and benefits

| Scenario | Result |
|---|---|
| `resident.onboarding.in_progress` | Completed/current/pending/blocked examples |
| `resident.onboarding.complete` | All required steps complete |
| `resident.onboarding.empty` | No assigned definition/steps according to safe contract behavior |
| `resident.onboarding.unavailable` | Stable dependency failure |
| `resident.benefits.typical` | Multiple applicable benefits with long Vietnamese content |
| `resident.benefits.empty` | No applicable benefits |

### Assistant

| Scenario | Result |
|---|---|
| `assistant.grounded_answer` | Vietnamese answer plus multiple citations |
| `assistant.unavailable_answer` | Approved unsupported-information response |
| `assistant.dependency_unavailable` | Model/knowledge dependency failure while manual tickets remain usable |
| `assistant.ticket_patch_empty_fields` | Subject/Content/Urgency proposal for unchanged empty draft |
| `assistant.ticket_patch_replacement_review` | Proposal for a non-empty or changed field |
| `assistant.ticket_patch_stale_fingerprint` | Stale observed fingerprint requiring explicit review |

### Persistent ticket draft

| Scenario | Result |
|---|---|
| `draft.none` | `GET` returns `204` |
| `draft.start.created` | New draft generation at version 1 |
| `draft.start.existing` | Existing active draft and updated timestamp |
| `draft.update.saved` | Accepted patch increments version |
| `draft.update.delayed_old_response` | Older response delivered after a newer accepted response |
| `draft.update.unavailable` | Network/dependency failure while unsaved buffer remains |
| `draft.update.conflict` | `409 ticket_draft_conflict` with current draft |
| `draft.replace.success` | New `draft_id`, version 1, empty Subject/Content, Normal urgency |
| `draft.generation_gone.unknown` | Generic `ticket_draft_generation_gone` without cause |
| `draft.generation_gone.submitted` | Generation gone with same-account proven ticket reference |
| `draft.submit.validation_error` | Field errors without consumed submission result |
| `draft.submit.success` | Created Pending ticket and no active draft |
| `draft.submit.transport_unknown_committed` | First response drops after commit; same-key retry returns ticket |
| `draft.submit.same_key_different_payload` | `409 idempotency_key_reused` |

Use two simulated browser contexts for the conflict scenarios so tests prove cross-session behavior rather than only calling a handler directly.

### Resident tickets and notifications

| Scenario | Result |
|---|---|
| `resident.tickets.empty` | Empty history |
| `resident.tickets.mixed_statuses` | Pending, Resolving, Resolved, and Denied rows |
| `resident.ticket.denied_detail` | Denial explanation and ordered events |
| `resident.notifications.empty` | Empty notification history |
| `resident.notifications.read_unread` | Mixed read state and related-resource references |
| `resident.notifications.read_failure` | Read mutation failure without losing list position |

### Profile and Zalo

| Scenario | Result |
|---|---|
| `profile.resident.typical` | Immutable identity/location plus editable metadata |
| `profile.manager.multi_building` | Multiple buildings and different floor grants |
| `profile.manager.no_scope` | Authenticated Manager with no grants |
| `profile.contact_change.otp` | Masked new-contact challenge |
| `profile.zalo.valid` | Normalized URL plus validator version |
| `profile.zalo.invalid` | `422 field_validation_failed` fixtures for policy boundaries |

Zalo fixtures test only the approved local syntax. Do not add handlers that claim profile existence, ownership, delivery, or read status.

### Manager residents and onboarding

| Scenario | Result |
|---|---|
| `manager.residents.typical` | Cursor page with multiple buildings/floors |
| `manager.residents.empty_scope` | No grants and no resident data |
| `manager.residents.scope_changed` | `409 scope_changed` requiring cache purge |
| `manager.onboarding.mixed_progress` | Complete, incomplete, and blocked examples |
| `manager.onboarding.unavailable` | Registry/progress dependency unavailable |

### Manager tickets

| Scenario | Result |
|---|---|
| `manager.tickets.queue` | Privacy-safe ticket rows across allowed filters |
| `manager.ticket.open.transitioned` | `PENDING -> RESOLVING` success |
| `manager.ticket.open.already_current` | Current Resolving or terminal detail without conflict |
| `manager.ticket.open.conflict` | `409 ticket_open_conflict` with safe current detail and notification |
| `manager.ticket.transition.resolved` | Successful terminal transition |
| `manager.ticket.transition.denied` | Successful Denied transition with explanation |
| `manager.ticket.transition.conflict` | `409 ticket_state_conflict` with current state |
| `manager.ticket.scope_revoked` | Existence-safe protected `404` or `scope_changed` requiring purge |
| `manager.ticket.zalo.success` | Scoped normalized URL response |
| `manager.ticket.zalo.fallback` | `outcome=notify_fallback` |

### Notification campaigns

| Scenario | Result |
|---|---|
| `notification.preview.ticket_resident` | Server-derived single-resident preview |
| `notification.preview.building_all_floors` | Whole-building preview for valid `ALL_FLOORS` scope |
| `notification.preview.floor` | Exact scoped floor preview |
| `notification.preview.unit` | Exact scoped unit preview |
| `notification.preview.selected_residents` | All selected residents in scope |
| `notification.preview.partial_unauthorized` | Whole preview rejected without partial audience disclosure |
| `notification.preview.empty` | Zero recipients; send unavailable |
| `notification.send.accepted` | `202` durable campaign acceptance |
| `notification.send.preview_stale` | `409 notification_preview_stale`; nothing sent |
| `notification.send.transport_retry` | First response drops; same-key retry returns original campaign |

## Delay and Failure Controls

Mocks should support bounded deterministic controls for:

- Initial response delay
- Mutation delay
- Offline/network failure before request send
- Transport failure after a simulated commit
- Out-of-order draft update responses
- Session expiry on the next protected request
- Scope change on the next scoped request
- Registry, OTP, assistant, or internal dependency failure

Avoid random failures in default tests. Randomized exploratory tests may supplement but must not replace deterministic scenarios.

## Contract Drift Checks

- Type-check fixtures against generated or validated API types.
- Fail tests when a mock includes fields rejected by the authoritative schema.
- Keep error codes aligned with the API contract.
- Validate the canonical assistant/draft fingerprint and submission-key fixtures against shared backend contract fixtures when those files are implemented.
- Validate `ZaloLinkPolicy v1` frontend assistance against the version-controlled backend policy fixtures; the frontend may not add accepted cases.

## Scenario Reset and Isolation

- Each test begins from a named deterministic scenario.
- Reset handler state, idempotency records, cursors, sessions, scope version, and draft generation between tests.
- Tests for retry semantics intentionally preserve the scenario's idempotency result across the retry within that test.
- Parallel tests use isolated accounts and draft IDs.

## Administrator Deferral

Do not create MVP frontend fixtures, pages, navigation, or handlers solely for administrator UI. Existing administrator backend contracts remain future scope and should be tested by the backend independently.

## Mock Readiness Checklist

- All 18 pages can render representative loading, empty, error, and success states.
- Draft conflict, generation-gone, and ambiguous submit scenarios are deterministic.
- Manager open/state conflicts and scope purge are deterministic.
- Notification preview/send retries and stale preview are deterministic.
- Fixtures contain only synthetic data.
- Mock and integrated modes use the same URL and TypeScript contract surface.
