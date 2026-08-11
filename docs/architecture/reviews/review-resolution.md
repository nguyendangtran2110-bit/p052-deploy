# Architecture Review Resolution

**Date:** 2026-08-11
**Participants:** PM, Architect, UX Designer

The three independent reviews remain unchanged as pre-fix evidence. This file records the disposition applied to the architecture set.

## Resolved in Architecture

| Review seam | Resolution |
|---|---|
| Concurrent detail opens | Observed status/version plus attempt idempotency distinguishes the winning transition, concurrent loser, and later normal view. |
| Ticket draft and submission retry | Zero or one PostgreSQL draft row per resident account, generation/version-bound mutations, atomic submit/delete, and durable same-key POST retry resolve concurrency and uncertainty. |
| `Notify` ambiguity | Ticket detail opens a resident-preselected composer; preview and explicit campaign send are canonical. |
| Session/device continuity | The persistent account draft survives session expiry, logout/login, and devices; account switch purges only client caches/buffers. |
| Administrator-created accounts | Administrator creates a pending activation reservation; user verifies OTP and chooses credentials. |
| Profile/contact ownership | Field edit matrix, verified contact replacement, password/session behavior, and symmetric manager endpoints are defined. |
| Registry claim transaction | Registry is read-only; OnBxrd owns the local atomic claim and account transaction. |
| Manager scope freshness | Refresh at login/session renewal/before mutations, 15-minute read window, fail-closed behavior, scope versioning, and cache purge are defined. |
| Notification audiences | Durable preview/campaign schema, `ALL_FLOORS` rule, stale-preview rejection, exact recipient snapshot, and idempotent fan-out are defined. |
| Onboarding versioning | Version-controlled immutable seeds, pinned enrollments, stable step keys, and explicit migrations are defined. |
| Browser/API topology | One public origin reverse-proxies `/api/*`; cookie, CSRF, CORS, and cache behavior are fixed. |
| Worker correctness | At-least-once leases, bounded retry, dead-letter state, and consumer idempotency are fixed. |
| Privacy-safe reads | Manager resident/onboarding/ticket response fields and pagination boundaries are minimized and documented. |
| Chroma operations | Single read-only runtime replica, versioned index switch, and assistant-only maintenance impact are explicit. |
| Prototype migration | Existing SQLite/demo state is classified as disposable and is not migrated. |
| Draft cardinality and lifecycle | The authoritative rule is zero or one active draft. There is no inactivity expiry in MVP; logout/session expiry preserve it, deactivation hides it, and restoration returns it. |
| Draft ABA race | Every mutation compares account, immutable `draft_id` generation, and expected version. Replacement creates a new generation atomically; stale generations cannot affect later drafts. |
| Submission ambiguity | Removed the unobservable `submission_processing`/status endpoint. A durable unique account/key result is committed with the ticket and draft deletion; clients retry the same POST/key. |
| Draft UX concurrency | Explicit-new versus direct-resume triggers, single-flight autosave, truthful save state, field-level reconciliation, assistant proposal provenance, and account/epoch-bound buffers are fixed. |
| Zalo executable boundary | `ZaloLinkPolicy v1` defines exact local syntax, versioned policy/fixture artifacts, stored validator version, stale-policy revalidation, and protected external opening. |
| Submission retry after reload | The key is deterministically derived and non-sensitive attempt metadata is stored in account-bound `sessionStorage`, so reload can retry even after committed draft deletion without persisting ticket fields. |

## Final Classification

- **Architecture blockers:** None. The authoritative PRD and architecture now agree on local rule-only Zalo validation and a zero-or-one persistent account-owned ticket draft.
- **Implementation dependencies:** Concrete `RegistryAdapter` transport/configuration, concrete `OtpService` provider/configuration, and exact dependency lockfiles.
- **Deployment/security blocker:** The previous credential-shaped `.env.example` value has been replaced, but possible rotation/revocation and repository-history/telemetry audit remain required before external deployment.

The explicitly deferred MVP topics remain deferred and did not drive new architecture scope.
