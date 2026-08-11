# Implementation Readiness

## Verdict

**PASS WITH CONCERNS**

The authoritative PRD and architecture now agree on rule-only `ZaloLinkPolicy v1` validation and a zero-or-one persistent account-owned ticket draft. The final reviewer findings on cardinality, draft-generation ABA safety, submission idempotency observability, draft retention, assistant provenance, and frontend conflict handling are resolved. No true architecture blockers remain. Registry and OTP details are implementation/configuration dependencies, while the possible credential exposure remains a deployment/security blocker only. [`../Brief.md`](../Brief.md) and [`../../PRODUCT.md`](../../PRODUCT.md) are legacy/supporting documents and do not block architecture.

## Architecture Decisions Complete

- Modular monolith and dependency direction.
- FastAPI/Python brownfield backend continuation.
- React/Next.js role-specific web client boundary.
- PostgreSQL source of truth and Alembic migration direction.
- Database-backed sessions, registry matching, OTP verification, and administrator bootstrap model.
- Local atomic identity claim plus administrator pending-activation model.
- Same-origin browser/API topology, cookie, CSRF, and CORS boundary.
- Exact manager building-floor/`ALL_FLOORS` scope.
- Manager scope refresh, bounded freshness, and revocation behavior.
- Immutable submitted ticket snapshots and historical access semantics.
- Zero or one persistent account-owned ticket draft shared across sessions/devices.
- Immutable draft-generation ID plus optimistic versioning, generation-aware conflicts, atomic replacement, and no-inactivity-expiry behavior.
- Durable account/key-to-ticket submission result with same-key POST retry and atomic ticket creation/draft clearing.
- MVP ticket schema and urgency enum.
- Automatic `PENDING -> RESOLVING` on full-detail open.
- Concurrent open and terminal first-valid-write-wins behavior with conflict notifications.
- Version-controlled `ZaloLinkPolicy v1`, stored validator version/revalidation, and outbound-only Zalo handoff without external verification.
- Durable notification campaign, audience preview/revalidation, fan-out, and read-state boundary.
- Versioned onboarding seeds, resident enrollment, and explicit migration behavior.
- Profile/contact ownership, verified edits, and password/session rules.
- WCAG 2.2 AA, responsive role shells, and minimum viewport/breakpoints.
- At-least-once worker/outbox semantics for reminders and notification fan-out.
- Single-replica read-only Chroma runtime and replacement behavior.
- Deployment, migrations, observability, health, backup, and rollback shape.

## Architecture Blockers

**None.** `FR-CHAT-002`, `FR-TKT-001`, `FR-TKT-002`, and `FR-TKT-006` now match `AD-006`, `AD-009`, `AD-010`, [`ADR-0004`](adr/ADR-0004-persistent-ticket-draft.md), and [`ADR-0006`](adr/ADR-0006-rule-based-zalo-validation.md). The generation identifier closes the ABA race, and the same-key POST retry protocol is observable under the single PostgreSQL transaction.

## Implementation Dependencies

### I-001 - Concrete registry adapter configuration

Implement the abstract `RegistryAdapter` contract in [`integrations.md`](integrations.md) against the selected API, database view, or versioned-file transport. Supply endpoint/connection details, credentials/access mode, stable IDs, active semantics, source version behavior, contact fields, resident location, and manager scope fields. These values are implementation/integration setup, not architecture decisions.

### I-002 - Concrete OTP provider configuration

Implement the abstract `OtpService` contract in [`integrations.md`](integrations.md). Select a provider and supply credentials, sender identity, environment/sandbox, delivery error mapping, and callback or verification mode during implementation setup. Provider-specific behavior is not required by the MVP.

### I-003 - Lock exact dependency patches

Commit frontend/backend lockfiles and compatible runtime/database patch versions within the documented compatibility envelope before the first reproducible build.

## Deployment/Security Blockers

### D-001 - Possible exposed credential

The prior `AI_LOG_API_KEY` value in `.env.example` was credential-shaped and has been replaced with a clearly fake placeholder. Because it may have been usable, rotate/revoke it and audit repository history and telemetry before any external deployment. Real secrets must never be committed, including in example files.

This item does not block architecture completion or local implementation work; it blocks external deployment.

## Implementation Concerns, Not Blockers

- Current routes trust client `actor_role` and current tests assert superseded ticket behavior; they must be replaced, not preserved.
- Current `src/services/mvp.py` uses an obsolete unscoped SQLite draft model and old states; do not reuse its schema/concurrency semantics for the new account-unique PostgreSQL draft.
- Existing SQLite/demo data is classified as disposable synthetic state and will not be migrated.
- No frontend project exists yet.
- Chroma's read-only local topology constrains the MVP assistant to one serving replica and an accepted index-switch maintenance window.
- Existing `docs/api.md`, `docs/deployment.md`, and tests are stale relative to this architecture and must not be used as acceptance authority.
- Persistent-draft frontend stories require the UX flow/state artifacts listed in [`frontend-architecture.md`](frontend-architecture.md): explicit-new versus direct-resume flow, autosave state machine, field-level conflict review, assistant proposal review, and session-expiry/account-switch behavior. These are bounded UX/story inputs, not architecture blockers.
- Assistant and submit fingerprints use the canonical UTF-8 NFC field representation defined in [`api-contracts.md`](api-contracts.md), preventing clients from inventing incompatible provenance or retry keys.
- Implementation must add the version-controlled `config/zalo/zalo-link-policy-v1.yaml` and `tests/fixtures/zalo-link-policy-v1.json` artifacts defined by the architecture; no vendor, credential, or endpoint is required.

## Deferred Post-MVP Items

- Benefit governance and chatbot-source governance.
- Notification type catalog and retention.
- Manager-registry maintenance ownership and workflow.
- KPI and quantitative performance targets.
- Document uploads and retention/security controls.
- External notification channels and live Zalo messaging, including profile-existence/ownership verification.
- Ticket attachments, categories, reopening, cancellation, escalation, and SLAs.

## Recommended Implementation Order

1. Establish PostgreSQL, Alembic, module skeletons, shared error model, and audit primitives.
2. Implement identity, local claims/invitations, abstract registry/OTP adapters, sessions, RBAC, and scope refresh predicates.
3. Scaffold the Next.js web client, API client, role shells, WCAG foundation, and responsive layout tokens.
4. Implement resident/manager profiles, verified contact/password changes, admin pending activation, and admin-controlled corrections/scope projection.
5. Implement the account-unique draft table/API, generation/version checks, resume/atomic-replace/discard flows, assistant patch provenance, single-flight frontend saving, and atomic submit/clear with durable same-key retry.
6. Implement submitted ticket snapshots, event history, observed-version open command, optimistic transitions, and conflict notifications.
7. Implement notification campaigns, ticket `Notify`, audience preview/revalidation/fan-out, notification center, and read/unread state.
8. Implement versioned onboarding seeds/enrollment/progress/reminder worker and read-only benefits.
9. Migrate grounded assistant behavior behind the adapter and remove demo routes/state.
10. Add deployment topology, production health/readiness, backup rehearsal, and security validation.
11. Run independent security, UX, test-architecture, and implementation-readiness reviews before production release.

## Acceptance Gate for Starting Stories

Architecture approval may proceed. Individual registration/authentication stories require I-001 and I-002 configuration before integration testing; I-003 is required before reproducible builds. No external deployment occurs until D-001 is resolved. Every story must cite the applicable architecture document/ADR and the approved PRD acceptance criteria.
