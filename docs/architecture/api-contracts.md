# API Contracts

## Conventions

- Base path: `/api/v1`.
- Browser requests use the same public origin; the edge proxies `/api/*` to FastAPI. Production credentialed CORS is disabled.
- JSON request/response bodies; UTF-8 Vietnamese text is supported end to end.
- Authentication uses the opaque session cookie; clients never send authoritative `actor_role`.
- Mutating requests require a CSRF token bound to the session.
- Timestamps use UTC ISO 8601; display localization belongs to the web client.
- IDs are opaque strings/UUIDs. Building/floor display numbers are not authorization IDs.
- Protected responses use `Cache-Control: no-store`; the frontend may cache only in-memory/query-cache state and must purge it on `scope_changed`, protected `404`, logout, or account switch.
- Validation and domain errors use:

```json
{
  "error": {
    "code": "stable_machine_code",
    "message": "localized user-safe message",
    "details": {},
    "request_id": "opaque-correlation-id"
  }
}
```

Do not include stack traces, raw provider errors, registry records, or protected object metadata.

## Authentication Surfaces

| Method | Path | Auth | Responsibility |
|---|---|---|---|
| `POST` | `/auth/register/resident` | Public, rate-limited | Match resident ID/contact and create OTP challenge |
| `POST` | `/auth/register/manager` | Public, rate-limited | Match manager ID/contact/scope and create OTP challenge |
| `POST` | `/auth/registrations/{challenge_id}/verify` | Public, challenge-bound | Verify OTP, atomically claim ID, create account/session |
| `POST` | `/auth/login` | Public, rate-limited | Verify username/password and create session |
| `POST` | `/auth/logout` | Authenticated | Revoke current session |
| `GET` | `/auth/me` | Authenticated | Return principal, role, profile summary, and display scope |
| `POST` | `/auth/recovery` | Public, rate-limited | Start registry-contact recovery challenge |
| `POST` | `/auth/recovery/{challenge_id}/complete` | Challenge-bound | Reset password after OTP verification |
| `GET` | `/auth/csrf` | Authenticated | Return a session-bound synchronizer token |
| `POST` | `/auth/contact-changes` | Authenticated | Start verified phone/email replacement |
| `POST` | `/auth/contact-changes/{challenge_id}/verify` | Authenticated, challenge-bound | Verify and commit new contact |
| `POST` | `/auth/password/change` | Authenticated | Change password and revoke other sessions |

Registration requests include username, password, phone, email, and resident/manager ID. The server chooses a matching registry contact destination and returns `challenge_id`, `channel`, `masked_destination`, and `expires_at`; the client never chooses an unmatched destination. A matching administrator-created invitation is consumed during verification. Responses never return registry contacts beyond the selected masked destination. An already active ID returns `409 identity_already_claimed` with login/recovery actions.

### Profile and credential mutations

```jsonc
// PATCH /resident/profile or /manager/profile
{"display_name": "optional string", "theme": "optional supported theme"}

// POST /auth/contact-changes
{"kind": "PHONE | EMAIL", "new_value": "string", "current_password": "string"}

// POST /auth/contact-changes/{challenge_id}/verify
{"code": "string"}

// POST /auth/password/change
{"current_password": "string", "new_password": "string"}
```

Profile payloads reject username, registry ID, resident location, manager grants, and unverified contact replacements. Successful contact verification replaces the account-owned recovery contact. Password change revokes all other sessions and rotates the current session/CSRF token.

## Resident Surfaces

| Method | Path | Responsibility |
|---|---|---|
| `GET` | `/resident/profile` | Return current verified profile and editable-field metadata |
| `PATCH` | `/resident/profile` | Update display name/preferences only; contacts use verified auth endpoints |
| `PUT` | `/resident/profile/zalo` | Normalize and rule-validate Zalo URL |
| `GET` | `/resident/onboarding` | Return current onboarding steps/progress |
| `POST` | `/resident/onboarding/{step_id}/complete` | Complete an allowed resident-controlled step |
| `GET` | `/resident/benefits` | Return applicable building benefits |
| `GET` | `/resident/tickets` | Return resident's current and historical tickets |
| `GET` | `/resident/tickets/{ticket_id}` | Return own ticket detail/history without state mutation |
| `GET` | `/resident/ticket-draft` | Return the authenticated resident's active draft or `204` |
| `POST` | `/resident/ticket-draft/start` | Idempotently create or return the one active account draft |
| `PATCH` | `/resident/ticket-draft` | Apply an optimistic field patch to the active draft |
| `POST` | `/resident/ticket-draft/replace` | Explicitly reset the expected active draft for a new ticket flow |
| `POST` | `/resident/ticket-draft/discard` | Explicitly delete the expected active draft |
| `POST` | `/resident/ticket-draft/submit` | Atomically create a ticket and clear the expected draft |
| `GET` | `/resident/notifications` | Return own in-app notifications |
| `POST` | `/resident/notifications/{id}/read` | Set read timestamp idempotently |

### Persistent ticket draft contract

The server derives the draft owner from the authenticated resident session. No draft endpoint accepts an account/resident ID. Anonymous, manager, administrator, and other-account access is unavailable.

`POST /resident/ticket-draft/start` requires an `Idempotency-Key` and returns:

```json
{
  "outcome": "created | existing",
  "draft": {
    "subject": "string",
    "content": "string",
    "urgency": "LOW | NORMAL | HIGH",
    "draft_id": "opaque-generation-id",
    "version": 3,
    "field_fingerprint": "base64url-sha256",
    "updated_at": "UTC timestamp"
  }
}
```

Concurrent starts rely on the unique account constraint and return the same row. `existing` is not an error; the frontend presents resume or confirmed replacement. Every draft representation returned by start/get/update/replace/conflict includes the server-computed `field_fingerprint` using the canonical representation defined below.

Draft update accepts only:

```json
{
  "draft_id": "opaque-generation-id",
  "expected_version": 3,
  "changes": {
    "subject": "optional string",
    "content": "optional string",
    "urgency": "optional LOW | NORMAL | HIGH"
  }
}
```

`replace`, `discard`, and `submit` use the same `draft_id` plus `expected_version` envelope without `changes`. `PATCH`, `replace`, `discard`, and `submit` require an `Idempotency-Key`. The server rejects resident name, phone, building, floor, room, status, role, or account ownership fields.

- A matching update increments the draft version and returns the accepted draft.
- A stale update returns `409 ticket_draft_conflict` with the current account-owned draft/version; it never silently merges or overwrites.
- A mutation for a no-longer-active generation returns generic `409 ticket_draft_generation_gone`; it may include the created same-account ticket only when a durable submission record proves it. MVP does not retain discarded/replaced draft history and does not claim the cause. The stale mutation never matches a later generation whose version may repeat.
- Replace resets subject/content, sets urgency to `NORMAL`, and atomically returns a new `draft_id` generation at version `1` in the same account slot. It requires prior explicit frontend confirmation but the backend still validates generation/version/idempotency.
- Discard deletes only the matching account/generation/version. Logout does not discard.
- Submit validates the matching draft, reads the current verified resident profile, creates the immutable ticket/snapshot/event, records the durable submission idempotency result, and deletes the draft in one transaction.
- A stale save after replace/discard/submit cannot recreate a draft; only `start` creates a draft generation.

Repeated committed submission requests with the same account/key and accepted fingerprint return the original ticket before requiring an active draft. Validation failures do not consume the submission key. For submit specifically, compute the reproducible key as base64url SHA-256 over UTF-8 `ticket-submit:v1`, `draft_id`, decimal `expected_version`, and the server-returned canonical field fingerprint, separated by literal unit-separator bytes. The frontend stores that non-sensitive attempt metadata in account-bound `sessionStorage` before sending, so a hard reload can retry even when the first request committed and deleted the draft. If transport fails after the request is sent, the client retries the same `POST` and same key; a concurrent retry is serialized by the durable uniqueness constraint and returns the original ticket after the first transaction commits. There is no separate submission-status endpoint or `submission_processing` response.

### Zalo link contract

`PUT /resident/profile/zalo` applies server-owned `ZaloLinkPolicy v1` and returns the normalized URL plus `validator_version`. The accepted MVP form is `https://zalo.me/<profile-id>` with exactly one ASCII `[A-Za-z0-9._-]{1,128}` segment; an optional trailing slash is removed. User-info, explicit ports, query, fragment, trailing-dot/IDNA host variants, encoded separators, malformed encoding, and control characters fail with `field_validation_failed`. The endpoint performs no network request.

`GET /manager/tickets/{ticket_id}/zalo` rechecks manager scope and revalidates any stored link whose validator version is not current. It returns either the current normalized URL or `outcome=notify_fallback`; it never returns an existence/ownership/delivery status. External navigation uses `noopener`, `noreferrer`, and no-referrer policy.

## Assistant Surface

`POST /resident/chat/messages` accepts the current message, bounded client conversation context, and the current draft context (`draft_id`, observed version, and field fingerprint) when ticket assistance is active. `field_fingerprint` is the base64url SHA-256 of UTF-8 NFC-normalized `subject`, `content`, and `urgency` joined in that order with the literal unit-separator byte; empty fields use the empty string and urgency uses its enum value. It returns:

```json
{
  "answer": "Vietnamese grounded answer or unavailable response",
  "citations": [{"label": "string", "source_ref": "opaque-reference"}],
  "ticket_patch": {
    "subject": "optional string",
    "content": "optional string",
    "urgency": "optional LOW | NORMAL | HIGH"
  },
  "missing_ticket_fields": ["subject"],
  "draft_context": {
    "draft_id": "opaque-generation-id",
    "observed_version": 3,
    "field_fingerprint": "opaque"
  }
}
```

The response never contains authoritative resident profile/location data and never submits a ticket. The frontend applies accepted assistant patches through the same versioned draft API only after confirming that the returned draft generation/version and field fingerprint still match; fields changed since observation become explicit replacement proposals. The assistant cannot mutate a draft before the resident chooses Resume or confirms Discard and start new.

## Manager Surfaces

| Method | Path | Responsibility |
|---|---|---|
| `GET` | `/manager/profile` | Return identity and read-only per-building scope |
| `PATCH` | `/manager/profile` | Update display name/preferences only; contacts use verified auth endpoints |
| `GET` | `/manager/residents` | Return current residents limited to current scope |
| `GET` | `/manager/onboarding` | Return resident progress limited to current scope |
| `GET` | `/manager/tickets` | Return tickets whose immutable snapshot matches current scope |
| `POST` | `/manager/tickets/{ticket_id}/open` | Authorize, return full detail, and idempotently transition `PENDING` to `RESOLVING` |
| `POST` | `/manager/tickets/{ticket_id}/transitions` | Apply `RESOLVED` or `DENIED` using expected version |
| `GET` | `/manager/tickets/{ticket_id}/zalo` | Return validated normalized URL or `notify` fallback state |
| `POST` | `/manager/tickets/{ticket_id}/notification-previews` | Prepare a resident-preselected `Notify` composer preview |
| `POST` | `/manager/notification-previews` | Resolve a scoped building/floor/unit/resident audience |
| `POST` | `/manager/notification-campaigns` | Recheck preview/scope and accept one idempotent send |
| `GET` | `/manager/notifications` | Return manager notifications including ticket conflicts |
| `POST` | `/manager/notifications/{id}/read` | Set read timestamp idempotently |

### Open detail command

- Safe list/prefetch APIs never call it.
- Require an `Idempotency-Key` plus `observed_status` and `expected_version` in the request.
- If the observation matches `PENDING`, compare-and-swap to `RESOLVING`, increment version, append an event, and return `outcome=transitioned`.
- If another manager won that same observed `PENDING` version, return `409 ticket_open_conflict` with the current safe detail and create one idempotent conflict notification for the losing manager. Replaying the winning attempt key returns its original success.
- If the request observed the current `RESOLVING`, `RESOLVED`, or `DENIED` status/version, return `outcome=already_current` without a transition or notification.
- If scope fails, return existence-safe `404` and do not mutate.

```json
{
  "observed_status": "PENDING",
  "expected_version": 1
}
```

### Terminal transition request

```json
{
  "target_status": "RESOLVED | DENIED",
  "expected_version": 4,
  "denial_explanation": "required only for DENIED"
}
```

The frontend confirmation dialog is required UX but not a trusted backend signal. The backend validates legal state, scope, version, and denial explanation.

On a stale version, return `409 ticket_state_conflict` with the current safe ticket state/version. Persist an idempotent `ticket_conflict` notification for the losing manager.

## Notification Preview and Send

Generic preview accepts one selector:

```json
{
  "subject": "string",
  "content": "string",
  "audience": {
    "kind": "BUILDING | FLOOR | UNIT | RESIDENTS",
    "building_id": "required except RESIDENTS",
    "floor_id": "required for FLOOR or UNIT",
    "unit_id": "required for UNIT",
    "resident_account_ids": ["required for RESIDENTS"]
  }
}
```

- `BUILDING` requires the manager's active `ALL_FLOORS` grant for that building.
- `FLOOR` and `UNIT` require the exact pair or matching building `ALL_FLOORS` grant.
- `RESIDENTS` resolves every selected resident against current scope; partial authorization fails the whole preview.
- Ticket `Notify` does not accept an audience. The server derives the ticket resident after current ticket-scope authorization.
- Ticket `Notify` targets the submitting resident account even if the resident has since moved; authorization remains based on the immutable ticket scope. Generic selectors use current resident location.

Preview returns `preview_token`, normalized audience summary, recipient count, opaque recipient-set hash, manager scope version, and expiry. It does not expose a bulk contact list.

Send accepts only `preview_token` and requires an `Idempotency-Key`. The server refreshes manager scope, re-resolves recipients, and compares the subject/content fingerprint, scope version, and recipient-set hash. Any difference returns `409 notification_preview_stale` and creates no campaign or recipient notification. Success returns `202` with the durable campaign ID; at-least-once worker fan-out is recipient-idempotent. Reusing the send key returns the original campaign and never sends twice.

## Privacy-Safe Read DTOs

All collection endpoints use cursor pagination:

```json
{"items": [], "next_cursor": "opaque-or-null"}
```

`limit` defaults to 25 and is capped at 100. Filters are allowlisted and server scope is always applied after filter parsing.

- Manager resident rows expose resident account ID, display name, building/floor/room display values, and onboarding completion summary. They do not expose email, phone, resident registry ID, or Zalo URL.
- Manager onboarding detail exposes the same identity/location summary, assigned definition version, step labels/order/completion state, and reminder state. It does not expose contact fields.
- Manager ticket rows expose ticket ID, subject, urgency, state, version, submitted timestamp, and immutable building/floor/room snapshot.
- Full manager ticket detail additionally exposes immutable resident name/phone snapshot, content, denial explanation when present, event history, and contact-action availability. The validated Zalo URL is returned only by the scoped Zalo endpoint.
- `/auth/me` and profile responses expose only the current account's immutable identifiers, editable-field metadata, verified contact masks/values appropriate to the owner, current location or scope summary, preferences, and `session_epoch`/`scope_version`.
- Notification list rows expose ID, type, localized display payload, related-resource reference, `read_at`, and creation time. Listing does not mark read; opening an item invokes the idempotent read endpoint.

## Administrator Surfaces

| Method | Path | Responsibility |
|---|---|---|
| `POST` | `/admin/accounts/residents` | Reserve eligible resident identity for pending activation |
| `POST` | `/admin/accounts/managers` | Reserve eligible manager identity for pending activation |
| `POST` | `/admin/account-invitations/{id}/cancel` | Cancel unused invitation and release reservation |
| `POST` | `/admin/accounts/{id}/deactivate` | Deactivate account and revoke sessions |
| `POST` | `/admin/accounts/{id}/restore` | Restore eligible account |
| `POST` | `/admin/residents/{id}/correct-location` | Apply approved current location correction with audit |
| `POST` | `/admin/managers/{id}/refresh-scope` | Trigger registry-derived scope refresh; cannot submit arbitrary grants |

Administrator creation requests contain role-appropriate registry ID only; the server derives contact/location/scope and returns invitation status plus a masked activation destination. Username/password are supplied only by the invited user during verified activation. No public administrator registration or direct manager-scope editor exists in MVP.

```json
{"registry_id": "resident-or-manager-id"}
```

Creation requires an `Idempotency-Key`. Success returns invitation ID, role, `pending_activation`, expiry, and masked registry contact. An active local claim returns `identity_already_claimed`; an existing compatible pending invitation returns the original invitation.

## Error Semantics

| HTTP | Example code | Meaning |
|---:|---|---|
| `400` | `invalid_request` | Malformed or semantically invalid request |
| `401` | `authentication_required` | Missing/expired/revoked session |
| `403` | `capability_denied` | Authenticated role lacks a non-sensitive capability |
| `404` | `resource_not_found` | Missing or out-of-scope protected resource |
| `404` | `ticket_draft_not_found` | The current account has no active draft |
| `409` | `identity_already_claimed` | Registry ID already has an account |
| `409` | `ticket_state_conflict` | Expected ticket version/status is stale |
| `409` | `ticket_open_conflict` | Another manager won the observed detail-open transition |
| `409` | `ticket_draft_conflict` | Another session changed the current draft generation |
| `409` | `ticket_draft_generation_gone` | The expected draft generation is no longer active; cause is not inferred without durable submission evidence |
| `409` | `notification_preview_stale` | Scope or resolved audience changed after preview |
| `409` | `scope_changed` | Session/client scope version is stale and protected caches must reset |
| `409` | `idempotency_key_reused` | Same key was presented with a different accepted payload |
| `422` | `field_validation_failed` | Valid JSON with invalid field values |
| `422` | `otp_invalid` / `otp_expired` | Challenge code is invalid or expired without identity disclosure |
| `423` | `otp_attempts_exhausted` | Challenge is invalidated after its bounded attempt count |
| `429` | `rate_limited` | Registration/login/OTP/provider protection |
| `429` | `otp_rate_limited` | OTP issue/resend must wait for returned retry timing |
| `502` | `dependency_unavailable` | Registry, OTP, LLM, or knowledge dependency failed safely |
| `503` | `temporarily_unavailable` | Required internal component not ready |

## Idempotency

- Required for draft start/update/replace/discard/submit, open-detail mutation, registration verification, OTP send/retry, administrator invitation creation/cancel, notification send, and worker delivery.
- Idempotency scope includes authenticated principal or registration challenge plus endpoint and key.
- Store request fingerprint, result reference, status, and expiry; reject reuse with a different payload. Submission mappings are durable for the ticket-history lifetime and are keyed by `(resident_account_id, idempotency_key)`; ordinary draft mutation records may expire sooner.
- Ticket-open attempts store their original result so a winning retry is not reclassified as a conflict.
- Ticket conflicts use a source-event/losing-manager key so retries create one notification.
- Draft mutation keys are scoped to the authenticated account, endpoint, and request fingerprint. Same-key retries return the original result; a different payload returns `idempotency_key_reused`.
- Submission keys remain stable through ambiguous network results and same-account reauthentication. They are bound to the account, source `draft_id`/version, and accepted payload fingerprint; the durable mapping returns the original ticket even though the active draft has been deleted.
