# Persistent Draft and Rule-Only Zalo Architecture Review

**Reviewer:** Winston, System Architect  
**Date:** 2026-08-11  
**Scope:** Domain, data, API, authentication/authorization, security, concurrency, migration, and readiness contracts for the persistent single-account ticket draft and local rule-only Zalo validation  
**Verdict:** **BLOCKED for persistent-draft implementation; Zalo is PASS WITH CONCERNS**

The revised architecture correctly moves the authoritative draft into PostgreSQL, scopes it to the authenticated resident account, supports cross-session/device access, rejects anonymous and cross-account access, and keeps Zalo free of external verification dependencies. Two load-bearing concurrency defects remain: stale requests can mutate a later draft generation, and the documented submission-status protocol cannot observe an in-flight submission under the stated single-transaction design.

The architecture spine linter passes with zero mechanical findings. The findings below are semantic and transactional.

## Blocking Findings

### B-001 - Account-plus-version comparison has an ABA race across draft deletion and recreation

**Evidence**

- `TicketDraft` has an ID in `docs/architecture/domain-model.md:90`, but draft API responses and mutation requests omit it at `docs/architecture/api-contracts.md:93` and `docs/architecture/api-contracts.md:110`.
- The compare-and-swap predicate uses only `resident_account_id` and `version` at `docs/architecture/data-architecture.md:131`.
- Submit and discard delete the row, while a later explicit start may create a new row at `docs/architecture/data-architecture.md:141` and `docs/architecture/data-architecture.md:143`.
- The architecture claims a stale save after deletion cannot affect a later draft at `docs/architecture/api-contracts.md:128`, but that claim is not enforced by the documented predicate.

**Failure sequence**

1. Session A reads draft `D1` at version `1`.
2. Session B submits or discards `D1`; the row is deleted.
3. A new ticket flow creates draft `D2`, also beginning at version `1`.
4. Session A sends a delayed update with `expected_version=1` and a fresh idempotency key.
5. `WHERE resident_account_id = account AND version = 1` matches `D2`, so the stale `D1` update overwrites the new draft.

This is the classic ABA problem. The unique account constraint guarantees one current row, but it does not identify the lifetime/generation of that row.

**Required resolution**

Preserve the product's delete-on-submit rule and bind every mutation to an immutable draft generation:

- return `draft_id` from start/get/update/replace responses;
- require `draft_id` plus `expected_version` on update, replace, discard, and submit;
- compare on `(resident_account_id, draft_id, version)` in every mutation;
- include `draft_id` in the idempotency request fingerprint;
- create a new unpredictable `draft_id` after discard or submission; and
- store the source `draft_id` on the submission idempotency record and, preferably, the created ticket/audit event.

A stale generation must return a stable consumed/replaced result and must never match a later row even if version numbers repeat.

### B-002 - `submission_processing` is not observable under the documented atomic transaction

**Evidence**

- `docs/architecture/api-contracts.md:132` promises `202 submission_processing` while the owning submit request is unresolved.
- `docs/architecture/data-architecture.md:143` says ticket creation, snapshot/event creation, submission-idempotency recording, and draft deletion occur in one transaction.
- `docs/architecture/api-contracts.md:127` repeats the same single-transaction rule.

**Impact**

Under normal PostgreSQL isolation, a submission-status request cannot see an uncommitted idempotency row owned by the in-flight ticket transaction. It will observe no record, not `processing`. Returning `404 submission_not_recorded` at that point would falsely authorize a retry/new key while the first transaction may still commit. If a separately committed processing row is intended, crash recovery and lease ownership are currently undefined.

**Required resolution**

Choose one concrete protocol:

1. Reserve `(resident_account_id, endpoint, idempotency_key)` in a short committed transaction with `processing`, payload fingerprint, owner/lease, and expiry.
2. In the business transaction, lock the reservation and matching draft generation/version; create ticket/snapshot/event, delete the draft, and change the reservation to `succeeded` with the ticket reference atomically.
3. A same-key concurrent POST or status GET returns `202` while the lease is live, `200` when succeeded, and may take over/retry after an expired processing lease.
4. Validation failure records a definitive retryable/non-accepted outcome without deleting the draft.

Alternatively, remove the status endpoint and `202` promise and require same-key POST retry until a committed result is visible. The current hybrid contract is not implementable as written.

## Important Findings

### I-001 - Conflict semantics are undefined when the expected draft no longer exists

`docs/architecture/data-architecture.md:141` and `docs/architecture/api-contracts.md:124` say a stale mutation returns the current account-owned draft. After another session submits or discards it, there is no current row. The error table contains both `ticket_draft_not_found` and `ticket_draft_conflict`, but it does not define which applies to update, replace, discard, or submit after consumption.

Define generation-aware outcomes:

- current generation, stale version: `409 ticket_draft_conflict` with the current draft;
- old/consumed generation: `409 ticket_draft_generation_gone` or equivalent, with `reason=SUBMITTED|DISCARDED|REPLACED` where safe;
- same-account submitted generation: optionally include the created ticket reference;
- no active draft and no known generation: `404 ticket_draft_not_found`.

The response must remain account-scoped and must not reveal another account's draft or submission.

### I-002 - Submission idempotency retention is too weak for the promised retry contract

`docs/architecture/api-contracts.md:295` gives generic idempotency records an expiry, while `docs/architecture/api-contracts.md:130` and `docs/architecture/api-contracts.md:299` promise that a committed submission always returns the original ticket after the draft has been deleted. No minimum retention or durable uniqueness rule is defined.

If the key/result expires, a delayed retry cannot resolve the original outcome. A later draft may also reuse the same key after expiry and create a different ticket.

Bind the durable invariant in data architecture:

- make `(resident_account_id, submission_idempotency_key)` unique on a durable ticket-submission record or the ticket itself;
- retain the key-to-ticket mapping for at least the ticket-history lifetime, or define an explicit supported retry horizon reflected in product/UX;
- never permit one account/key to reference two tickets; and
- distinguish shorter-lived idempotency records for ordinary draft updates from durable submission results.

### I-003 - Draft retention and cleanup behavior is not a complete data-lifecycle decision

`docs/architecture/data-architecture.md:160` says an active draft remains until submission, discard/replacement, or "account lifecycle cleanup." Deactivation explicitly preserves it at `docs/architecture/authentication-authorization.md:108`, and permanent account deletion is not an MVP capability. No automatic expiry or cleanup trigger is defined.

Because drafts contain sensitive resident issue descriptions and are included in backups, implementations could retain them forever or introduce incompatible TTLs. State one MVP rule explicitly:

- either active drafts do not automatically expire and remain until owner action/account deletion policy; or
- define a concrete inactivity TTL, warning behavior, recovery window, and audited deletion job.

Do not leave this to a repository implementation story.

### I-004 - The Zalo rule set is a placeholder rather than an executable validation contract

The rule-only boundary is correct, but `docs/architecture/integrations.md:126` refers to "approved Zalo hosts and profile-path patterns" without listing or locating the approval set. `ResidentProfile` stores validation time/status at `docs/architecture/domain-model.md:38`, but it does not store the validator-rule version, and the manager handoff does not explicitly revalidate links accepted under older rules.

Since local validation is the sole safety control, define:

- the initial host/path/query/fragment/port allowlist in version-controlled configuration;
- URL parsing, IDNA, percent-encoding, trailing-dot, user-info, and canonicalization test vectors;
- a `validator_version` stored with the normalized URL;
- revalidation on link edit and before manager handoff when the stored validator version is stale; and
- protected external opening (`noopener`, `noreferrer`, and an explicit referrer policy where applicable).

No Zalo API or profile-existence request is needed. This finding tightens the approved rule-only design rather than reopening it.

### I-005 - Ticket snapshot reads need one coherent profile/contact version

Submission reads verified phone from `Account` and name/location from `ResidentProfile`, then creates an immutable snapshot. The artifacts say this occurs in one transaction but do not define row locking or a shared projection version. A concurrent verified-contact change or administrator/registry location correction can produce a mixed snapshot assembled from different logical profile moments.

The submit transaction should lock/read the account contact and resident profile rows in a fixed order, or require one profile projection version and retry if it changes. The immutable ticket must contain one coherent accepted identity/location snapshot.

## Advisory Findings

### A-001 - Client mutation ordering needs an explicit monotonic response rule

`docs/architecture/frontend-architecture.md:58` uses a fresh key and rendered version for every mutation, but it does not explicitly serialize autosaves. Two in-flight saves from one tab can conflict with each other, and a delayed idempotent replay can return an older accepted response after a newer version is already displayed.

Require at most one in-flight mutation per draft generation, coalesce later keystrokes, and apply a response to the cache only when its `(draft_id, version)` is not older than the cached baseline.

### A-002 - The authoritative PRD uses both "at most one" and "exactly one"

`docs/PRD.md:330` correctly says an account has at most one active draft, while `docs/PRD.md:623` says every authenticated account has exactly one active draft. After submission or discard, the architecture intentionally allows no row until start.

PM should change the summary wording to "at most one active draft" or "exactly one while a ticket-creation flow is active" so implementation does not eagerly create blank drafts for every resident account.

## Consistency Matrix

| Review area | Result | Notes |
|---|---|---|
| Unique active account row | **Pass** | PostgreSQL uniqueness and authenticated-account ownership are consistent. |
| Start/resume/replace/discard/update | **Partial** | Operations exist and replace increments the same row, but generation identity is missing from mutation contracts. |
| Optimistic versioning | **Fail across generations** | Version CAS is correct within one row lifetime but vulnerable to ABA after delete/recreate. |
| Mutation idempotency | **Partial** | Account/endpoint/fingerprint scoping is good; submission processing and result retention are incomplete. |
| Atomic ticket creation and draft deletion | **Pass with condition** | The core business transaction is sound once it locks the exact draft generation and coherent profile snapshot. |
| Cross-session/device access | **Pass** | Account ownership, server persistence, refetch, and cache-purge behavior are aligned. |
| Account isolation | **Pass** | No account selector is accepted; current principal owns all draft and submission lookups. |
| Anonymous/manager/admin denial | **Pass** | RBAC and endpoint contracts consistently limit draft capability to active residents. |
| Persistent-data security | **Partial** | Logging/browser storage controls are strong; draft retention remains undefined. |
| Rule-only Zalo | **Pass with concerns** | No external verification or delivery claim; executable allowlist/versioning remains missing. |
| Prototype migration | **Pass** | SQLite demo drafts/tickets are explicitly disposable and not migrated. |
| Implementation readiness | **Fail for draft stories** | Readiness cannot be `PASS WITH CONCERNS` until B-001 and B-002 are resolved. |

## Migration and Test Gate

Before the persistent-draft story is implementation-ready, the migration/test contract should require:

- a unique `ticket_draft.resident_account_id` constraint and immutable draft-generation ID;
- positive/monotonic version constraints and compare-and-swap on account, generation, and version;
- durable unique `(account, submission_key)` result mapping;
- foreign-key/delete behavior that cannot transfer a draft to another account;
- tests for concurrent start, update/update, replace/update, discard/update, submit/update, submit/submit with same key, submit/submit with different keys, and start-new/stale-old-update ABA;
- tests for session expiry, logout/login, another device, account switch, deactivation/restoration, anonymous access, manager/admin denial, and cross-account submission-key lookup;
- transaction-failure tests between ticket, event, idempotency result, and draft deletion; and
- Zalo parser test vectors covering accepted canonical forms and malicious encoding/host/path cases without any network call.

## Final Verdict

**BLOCKED for persistent-draft implementation.** Fix the draft-generation ABA defect and choose an observable, crash-recoverable submission-idempotency protocol before accepting the architecture as implementation-ready. After those changes, the remaining draft findings are bounded clarifications.

**Rule-only Zalo is PASS WITH CONCERNS.** The architectural boundary is correct and consistent with the authoritative PRD; the initial versioned allowlist and revalidation rule must be made executable before the Zalo profile story begins.
