# Data Architecture

## Source-of-Truth Model

PostgreSQL is the product system of record. External registry data is authoritative for identity eligibility, resident location, and manager scope at claim/synchronization time; OnBxrd stores references and local projections needed for authorization and history.

Chroma remains an MVP knowledge index behind the assistant adapter. It is not authoritative for identity, permissions, tickets, benefits, onboarding, or notifications.

## Persistent Data

| Data | Storage | Key invariants |
|---|---|---|
| Accounts, password hashes, verified contacts | PostgreSQL | Immutable username/registry ID; unique local claim |
| Sessions | PostgreSQL | Opaque token hash, account, expiry, revocation |
| Registration challenges | PostgreSQL | Hashed OTP, bounded attempts, expiry, purpose |
| Activation invitations/claim reservations | PostgreSQL | Admin-created pending activation; no administrator-known password |
| Resident profiles | PostgreSQL projection | Current location is admin/registry controlled |
| Manager profiles and scope grants | PostgreSQL projection | Exact pair or `ALL_FLOORS` per building |
| Onboarding definitions/progress | PostgreSQL | Versioned definitions and persisted resident progress |
| Benefits | PostgreSQL | Resident-readable projection; governance deferred |
| Active ticket drafts | PostgreSQL | Zero or one row per resident account; immutable generation ID plus optimistic version |
| Ticket submission results | PostgreSQL | Durable unique account/key-to-ticket mapping for retry safety |
| Tickets and events | PostgreSQL | Immutable submitted snapshot; optimistic version |
| Notification campaigns and recipients | PostgreSQL | Authorized selector/preview plus one idempotent recipient record |
| Outbox/jobs | PostgreSQL | At-least-once lease state and consumer idempotency |
| Audit events | PostgreSQL | Append-only actor/action/resource/time metadata |
| Knowledge index metadata | Chroma plus configuration | Adapter-owned, not a product source of truth |

## Persistent Ticket Draft

Use zero or one active row per authenticated resident account:

```text
ticket_draft(
  draft_id UUID PRIMARY KEY,
  resident_account_id UNIQUE,
  subject,
  content,
  urgency,
  version,
  created_at,
  updated_at
)
```

The row contains only editable ticket fields. `draft_id` is immutable for one draft generation and unpredictable. Resident name, phone, room, floor, and building remain read-only profile data and are snapshotted only during submission. Logout, session expiry, refresh, and device/browser changes do not delete the row. Explicit discard deletes it; explicit replacement atomically installs a new generation ID with version `1` in the same unique account slot.

Submission outcomes use a separate durable mapping:

```text
ticket_submission(
  resident_account_id,
  idempotency_key,
  request_fingerprint,
  source_draft_id,
  source_draft_version,
  ticket_id UNIQUE,
  committed_at,
  PRIMARY KEY (resident_account_id, idempotency_key)
)
```

This mapping is retained with ticket history. One account/key can never identify two tickets.

## Transient Data

### Frontend edit buffer

The browser may hold current unsaved keystrokes, save/conflict UI state, and pending mutation keys in memory. This buffer is bound to the server-confirmed account/session epoch, is never the authoritative draft, and is purged before a different account renders. A single-flight/coalescing queue permits at most one mutation in flight for a draft generation. Internal route changes await the current save or require explicit leave confirmation; only the exact values acknowledged by the API are shown as `Saved` and guaranteed to survive a crash or network failure.

For an in-flight submit only, `sessionStorage` may persist non-sensitive recovery metadata: confirmed account ID, `draft_id`, expected version, field fingerprint, idempotency key, and start time. It must contain no ticket/profile/location fields, is restored only after `/auth/me` confirms the same account, and is cleared on definitive result or account switch. This is retry metadata, not an authoritative or reusable draft.

### OTP plaintext

Plaintext OTP values exist only during provider send and user entry. Store only a keyed hash, expiry, and attempt metadata.

### LLM request context

The MVP does not require persistent raw chat transcripts. The web client may send the current bounded conversation context; the backend must not log raw prompts, ticket content, or model chain-of-thought. Chat retention is not introduced implicitly by the architecture.

## Ticket Snapshot Schema

At submission, the backend locks/reads the account contact and resident profile rows in a fixed order inside the ticket transaction, then writes one coherent snapshot:

- resident account ID;
- resident name;
- resident phone;
- building internal ID and display number;
- floor internal ID and display number;
- unit/room internal ID and display value;
- subject, content, urgency; and
- initial `PENDING` state with version `1`.

Client-supplied resident/location values are ignored even if present.

## Manager Scope Representation

Use a normalized grant table with a database uniqueness constraint:

```text
manager_scope_grant(
  manager_account_id,
  building_id,
  floor_id nullable,
  all_floors boolean,
  source_registry_version,
  active_from,
  revoked_at
)
```

Constraints:

- exactly one of `floor_id` or `all_floors=true` is active;
- grants are unique per manager/building/floor mode;
- all scope-aware queries join on building and floor together;
- `ALL_FLOORS` applies only to its building;
- client filters never expand server authorization.

## Zalo Link Validation Data

Resident profiles store only the normalized URL, local validation status/timestamp, and `validator_version`. MVP uses `ZaloLinkPolicy v1` from `config/zalo/zalo-link-policy-v1.yaml` and its version-controlled contract fixtures. Profile edits always revalidate locally; manager handoff revalidates when the stored policy version is stale. No profile-existence, ownership, or delivery result is stored.

## Concurrency-Sensitive Data

### Registry identity claim

OnBxrd PostgreSQL owns the MVP claim ledger. A unique constraint on `(role, registry_identity_id)` plus one local transaction prevents two accounts claiming one ID. The transaction consumes a verified challenge or pending administrator invitation, creates the account/profile, activates the claim, and stores the registry source version. It issues a session only after commit. The external registry is read-only; no distributed transaction is claimed.

An administrator-created reservation has an expiry and no credentials. Activation uses the same OTP and local transaction. A crash before commit leaves the challenge/reservation retryable; a retry with the same idempotency key returns the committed account or safely retries. Expired/cancelled reservations are released by an audited idempotent job.

### Ticket transition

Updates use a compare-and-swap condition:

```text
UPDATE ticket
SET status = :next_status, version = version + 1, updated_at = now()
WHERE id = :id
  AND version = :expected_version
  AND status = :expected_status;
```

Zero updated rows means stale state or invalid transition. The API reloads the current ticket, returns a conflict response, and creates an in-app notification for the losing manager using an idempotent source key.

For open-detail, the compare-and-swap includes the client's observed `PENDING` status/version. The winning attempt result is stored by attempt key. A different manager presenting the same stale observation receives `ticket_open_conflict`; a later request that presents the current `RESOLVING` status/version is not a conflict.

### Active ticket draft

The unique `resident_account_id` constraint prevents multiple active rows. Start uses insert-on-conflict plus read so concurrent sessions receive the same draft.

Every update, replace, discard, and submit includes `draft_id`, `expected_version`, and an idempotency key. Updates use compare-and-swap:

```text
UPDATE ticket_draft
SET subject = :subject,
    content = :content,
    urgency = :urgency,
    version = version + 1,
    updated_at = now()
WHERE resident_account_id = :account_id
  AND draft_id = :draft_id
  AND version = :expected_version;
```

If the same generation still exists at another version, zero updated rows returns `ticket_draft_conflict` with the current account-owned draft. If the supplied generation is no longer active, return generic `ticket_draft_generation_gone`; include a same-account ticket reference only when a durable `TicketSubmission` record proves that generation was submitted. MVP does not retain discarded/replaced draft history and therefore does not claim which of those events occurred. If the account has no active draft and the supplied generation cannot be associated safely, return `ticket_draft_not_found`. These lookups never reveal another account's state.

The client must visibly reconcile a version conflict; it never silently overwrites. Replacement requires explicit UX confirmation and atomically changes `draft_id` while preserving the one-row account constraint. Discard deletes only the matching account/generation/version. A stale old-generation request therefore cannot match a later draft even when its version is also `1`.

Submission first checks the durable `(resident_account_id, idempotency_key)` result. A committed matching fingerprint returns its original ticket; reuse with a different fingerprint fails. Otherwise one transaction locks the matching account/draft-generation/version and coherent profile rows, creates the ticket/snapshot/event, inserts the durable submission result, and deletes the draft. The database uniqueness constraint serializes concurrent same-key submissions: a retry waits for the first transaction and then returns its committed result, or proceeds if the first rolled back. There is no separately visible `processing` state or status endpoint.

A concurrent stale save cannot recreate the deleted row; only an explicit start command may create a new generation. Draft mutation idempotency records are short-lived operational data, but submission key-to-ticket mappings are retained for the ticket-history lifetime.

### Notification fan-out and reminders

Use a PostgreSQL outbox/job table committed in the same transaction as the source event. Rows include `state`, `not_before`, `attempt_count`, `lease_owner`, `lease_expires_at`, `last_error_code`, and a unique source/consumer key. Workers claim due rows with `FOR UPDATE SKIP LOCKED` or an equivalent atomic lease, process at least once, retry with bounded backoff, and move exhausted poison jobs to `dead` for operational repair. Consumer uniqueness prevents duplicate campaign recipients, reminder notifications, and conflict notifications.

### Notification preview and send

Persist a short-lived preview record containing the normalized selector, author account, manager scope version, resolved recipient IDs/hash/count, subject/content fingerprint, and expiry. Send rechecks the manager's current scope and resolves recipients again in one transaction. If the scope version or recipient hash differs, return `notification_preview_stale` and create no campaign/outbox row. An accepted send persists the campaign, exact recipient snapshot, and fan-out outbox atomically. The send idempotency key returns the original campaign on retry.

### Onboarding definition publication

Version-controlled `config/onboarding/*.yaml` seed files are schema/checksum validated during deployment and published as immutable database definition versions. A unique `(building_id, definition_version, step_key)` identity prevents accidental duplicates. Resident enrollment stores the assigned version. An explicit migration operation carries completed timestamps by stable step key, retains retired-step history, and recalculates reminder jobs in the same transaction.

## Retention Assumptions

- Ticket snapshots/events and account/security audits are persistent product history for MVP; deletion policy requires later product/security approval.
- An active draft has no inactivity expiry in MVP and persists until successful submission, explicit discard/replacement, or a future permanent-account-deletion policy. Deactivation makes it inaccessible but does not delete it or expose it to administrators or another account; restoration returns the same draft.
- Notification retention is explicitly deferred. The MVP schema supports later purge/archival by `created_at` and does not promise a delete workflow.
- OTP challenges expire operationally and may be purged after their security/audit window.
- No onboarding document binaries are collected.
- Raw Zalo URLs and ticket content are excluded from routine logs.

## Migration from Current Prototype

- Replace `data/onbxrd_demo.db` and runtime table creation with PostgreSQL migrations.
- Treat the existing SQLite contents as disposable synthetic prototype state. Do not migrate demo drafts or tickets; create the new account-unique draft schema through PostgreSQL migrations.
- Do not support or map the obsolete state machine at runtime.
- Remove hard-coded `PROFILE` data and client-provided `actor_role` as authority.
