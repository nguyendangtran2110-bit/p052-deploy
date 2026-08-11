# Architect Spine Review

**Reviewer:** Winston, System Architect  
**Date:** 2026-08-11  
**Scope:** `docs/architecture/ARCHITECTURE-SPINE.md`, the complete `docs/architecture/` artifact set, current repository implementation, and active product documents  
**Verdict:** **BLOCKED**

The spine has a sound modular-monolith core and strong ticket/scope invariants, but it is not yet a safe implementation consistency contract. The highest-risk gaps are not stylistic: the durable product authority contradicts the architecture, the registry claim cannot be made atomic as currently written, and several cross-unit contracts still permit incompatible authentication, authorization, notification, and onboarding implementations.

## Review Method

- Ran the architecture spine linter. Result: `ok: true`, zero mechanical findings.
- Walked the good-spine rubric: divergence prevention, enforceability, deferred-item safety, brownfield fit, product traceability, technology currency, and operational completeness.
- Compared the architecture against `docs/PRD.md`, `docs/Brief.md`, `PRODUCT.md`, the existing FastAPI/SQLite/LangGraph implementation, dependency manifests, Docker/Compose, and CI.
- Checked current package registries on 2026-08-11 for named technology currency. Observed: FastAPI `0.141.1`, Alembic `1.19.1`, Next.js `16.3.0` with Node `>=20.9.0`, and React `19.2.8`.

## What Is Strong

- The modular-monolith paradigm and inward dependency direction are appropriate for the brownfield repository and MVP scale.
- PostgreSQL as product source of truth is justified by identity uniqueness, exact scope joins, ticket compare-and-swap, notifications, and audit history.
- Exact `(building, floor)` grants plus per-building `ALL_FLOORS` avoid the common cross-product authorization defect.
- Immutable ticket snapshots correctly preserve history through resident moves and allow newly scoped managers to access older tickets.
- The session-only ticket workspace is consistent with the approved transient-data behavior and keeps authoritative profile data server-side.
- The ticket state command separates side-effect-free queue reads from the automatic full-detail transition and protects terminal transitions with optimistic concurrency.
- The Zalo boundary is honest and safe: local validation only, no remote existence check, no delivery claims, and no provider credential dependency.
- Trust boundaries, logging redaction, database migrations, health checks, rollback shape, and WCAG/responsive constraints are materially better than the current prototype.

## Critical Findings

### C-001 - The architecture has no reconciled durable product authority

**Evidence**

- `docs/architecture/README.md:6` says the architecture is sourced from `docs/PRD.md` plus decisions captured during Party Mode.
- `docs/PRD.md:15` explicitly says it is not an approved implementation contract, and `docs/PRD.md:654` explicitly prohibits architecture freeze and executable stories.
- The PRD still requires or proposes behavior contradicted by adopted architecture: explicit `Start Resolving` at `docs/PRD.md:364`, profile-existence verification at `docs/PRD.md:408`, unresolved draft persistence at `docs/PRD.md:333`, and a completion note at `docs/PRD.md:369`.
- `docs/Brief.md:188`, `docs/Brief.md:192`, and `docs/Brief.md:193` still recommend invitation-only managers, server-side drafts, and explicit resolving actions.
- `PRODUCT.md:30`, `PRODUCT.md:34`, and `PRODUCT.md:36` still define Zalo group ingestion, pgvector, and the obsolete ticket lifecycle.

**Impact**

The explicit user decisions have higher authority than these files, so the architecture may reflect the intended product. Implementation agents, however, cannot reconstruct authoritative chat history reliably and will encounter mutually exclusive written requirements. This violates the project planning gate and makes `docs/architecture/README.md:10` and the partial-start allowance in `docs/architecture/implementation-readiness.md` unsafe.

**Required resolution**

1. Update and approve the PRD with the settled decisions, or create a formally approved decision addendum that the PRD incorporates by reference.
2. Reconcile `docs/Brief.md` and `PRODUCT.md`, or mark them explicitly superseded with pointers to the approved source.
3. Re-run product-to-architecture traceability before any implementation story begins.
4. Until this is done, all production implementation is blocked, not only registry/OTP stories.

### C-002 - Atomic identity claim is asserted across systems without an achievable transaction protocol

**Evidence**

- `docs/architecture/ARCHITECTURE-SPINE.md:27` requires an atomic ID claim.
- `docs/architecture/authentication-authorization.md:16` says registry claim, PostgreSQL account/profile creation, and session creation happen "in one transaction."
- `docs/architecture/data-architecture.md:92` protects only the local PostgreSQL claim.
- `docs/architecture/integrations.md:38` introduces an external `claim_identity` operation, while `docs/architecture/integrations.md:41` alternatively permits a local claim ledger.
- `docs/architecture/integrations.md:49` delegates partial-failure recovery to unspecified "transaction/outbox compensation."

**Impact**

A PostgreSQL transaction cannot atomically commit an external registry mutation. A crash after one side commits can leave an unusable claimed identity, duplicate eligibility, or an active account whose external scope was never claimed. The current artifacts also disagree on whether the registry or OnBxrd owns claim state.

**Required resolution**

Choose and record one claim protocol before authentication implementation:

- define the authoritative owner of claim state;
- define reservation/claim/finalize states and idempotency keys;
- keep the account non-active and issue no session until the protocol reaches its committed state;
- define crash recovery, replay, timeout, release, and manual reconciliation behavior; and
- make administrator-created resident/manager accounts use the same protocol.

`B-001` correctly identifies the missing external contract, but the architecture must not describe the unresolved cross-system operation as one transaction.

## High Findings

### H-001 - Browser-to-API origin topology is ambiguous for cookie sessions and CSRF

**Evidence**

- `docs/architecture/system-context.md:26` shows the browser calling the API directly.
- `docs/architecture/container-architecture.md:31` and `docs/architecture/deployment.md:25` show the web container calling the API.
- `docs/architecture/authentication-authorization.md:5` binds `SameSite=Lax` cookie sessions, and `docs/architecture/api-contracts.md:8` requires CSRF tokens.
- No document chooses a same-origin reverse proxy/BFF path or a direct cross-origin browser/API deployment contract.

**Impact**

The choice changes cookie domain/path/security settings, CORS, CSRF issuance and validation, credential forwarding, request IP/rate-limit semantics, local development, and deployment routing. Frontend and backend teams can implement individually reasonable but incompatible models.

**Required resolution**

Create an ADR choosing one browser access pattern. The lowest-risk MVP choice is one public origin with `/api/*` reverse-proxied to FastAPI; if direct cross-origin calls are chosen, specify the exact same-site domain model, credentialed CORS allowlist, preflight behavior, cookie attributes, and CSRF bootstrap flow.

### H-002 - Registry projection freshness is deferred even though it is an authorization invariant

**Evidence**

- `docs/architecture/data-architecture.md:5` makes registry data authoritative at claim/synchronization time.
- `docs/architecture/authentication-authorization.md:65` authorizes using current local profile/grant projections.
- `docs/architecture/data-architecture.md:74` records a registry version, but no refresh trigger or stale-data policy consumes it.
- `docs/architecture/authentication-authorization.md:67` says revoked grants remove access only after an updated projection is applied.
- Manager-registry maintenance is deferred in `docs/architecture/ARCHITECTURE-SPINE.md:92`.

**Impact**

Organizational maintenance ownership can be deferred, but runtime authorization freshness cannot. One implementation may refresh on every request, another only at registration, and another through an administrator action. A removed manager could retain access indefinitely in the last two cases.

**Required resolution**

Separate deferred maintenance governance from the required consumption contract. Define the minimum MVP projection-refresh trigger, maximum accepted staleness or explicit static-scope limitation, registry-version compare behavior, failure posture, and session/access response when scope is revoked. If no update feed exists, state that as a known security limitation requiring explicit PM/Security acceptance.

### H-003 - Targeted notifications have no aggregate, audience contract, or preview/send concurrency rule

**Evidence**

- `docs/architecture/domain-model.md:105` defines only a per-recipient `Notification` record.
- `docs/architecture/api-contracts.md:100` and `docs/architecture/api-contracts.md:101` list preview/send endpoints without request or response schemas.
- `docs/architecture/data-architecture.md:110` requires asynchronous fan-out but defines no durable parent message/campaign or audience snapshot.
- `docs/architecture/frontend-architecture.md:108` requires handling an audience change after preview, but no API token, version, or conflict condition exists.

**Impact**

Implementations can disagree on whether building targeting includes only assigned floors or requires `ALL_FLOORS`, what exactly was previewed, whether send proceeds after the audience changes, how subject/content is audited, and how retries avoid duplicate recipient records. Per-recipient rows alone do not preserve the manager's original send intent cleanly.

**Required resolution**

Define a durable manager-authored notification message/campaign entity, audience selector schema, authorized resolution rules, preview result/version, send-time compare behavior, recipient snapshot or reproducible resolution record, and outbox/idempotency transaction. Explicitly define whole-building targeting: only a matching `ALL_FLOORS` grant may target the full building; partial-floor managers may target only their authorized floors.

### H-004 - Configurable onboarding has no definition lifecycle or configuration input boundary

**Evidence**

- `docs/architecture/domain-model.md:63` calls onboarding definitions building-scoped and versionable.
- `docs/architecture/data-architecture.md:18` persists definitions and resident progress.
- There is no API, operational configuration source, activation rule, or ADR describing how definitions are created, revised, retired, or assigned.
- There is no rule for carrying completed progress forward when a definition changes or for deciding when a new required step makes an existing resident incomplete again.

**Impact**

The product requires configurable onboarding and automated reminders. Different implementations can silently reset progress, orphan progress, omit new steps, or send contradictory reminders. This topic was not among the product areas explicitly deferred from MVP architecture.

**Required resolution**

Define the MVP authoring boundary (for example, versioned operational seed/configuration rather than a new admin UI), immutable published versions, resident enrollment/version assignment, step identity across versions, add/reorder/retire semantics, progress carry-forward, and reminder recalculation. Product must decide any behavior that changes resident completion obligations.

### H-005 - Contact/profile data ownership and administrator-created account activation are unresolved

**Evidence**

- `docs/architecture/domain-model.md:27` stores phone/email on `Account`, while `docs/architecture/domain-model.md:36` stores them again on `ResidentProfile`; manager profiles also contain contact fields.
- Registry phone/email are used for signup and recovery in `docs/architecture/authentication-authorization.md:13` and `docs/architecture/authentication-authorization.md:39`.
- `docs/architecture/api-contracts.md:46` permits resident contact edits, but no manager profile update endpoint is defined despite the approved symmetric editability rule.
- `docs/architecture/api-contracts.md:129` and `docs/architecture/api-contracts.md:130` let administrators create accounts without defining username/password ownership, OTP activation, credential delivery, or claimed-ID behavior.

**Impact**

An implementation must invent whether an edited phone/email becomes a recovery factor, whether it updates the registry projection, which copy is used for ticket snapshots, and how an admin-created account becomes usable without exposing a password. Duplicate contact stores can drift.

**Required resolution**

Define separate fields and authority for registry verification contact, account recovery contact, and user-editable display/contact data; define verification requirements for edits; expose symmetric permitted manager profile edits; and define admin-created accounts as a concrete pending-activation/credential-establishment flow using the same identity claim invariant.

### H-006 - Major API surfaces are endpoint lists, not sufficient privacy-safe contracts

**Evidence**

- Ticket submission and assistant patching have useful schemas, but manager resident lists, onboarding views, ticket detail, notification preview/send, profile responses, administrator audit, and most list pagination/filter responses do not.
- `docs/architecture/security.md` classifies contact, location, ticket content, and notification payloads as sensitive, while the response-field minimization rules are not specified.
- The product decision on which resident fields managers may see remains unresolved; the architecture nonetheless presents the manager resident surface as implementation-ready.

**Impact**

Backend and frontend implementations can diverge in field names, pagination, authorization behavior, data exposure, stale-state handling, and audit semantics. The undefined manager-visible resident field set is a privacy decision, not an implementation detail.

**Required resolution**

Add request/response DTOs for every MVP mutation and cross-role read, including pagination/filter envelopes and version fields. PM must approve the minimal manager-visible resident data set. Until then, manager resident-directory and onboarding-detail stories remain blocked even if ticket work proceeds.

## Medium Findings

### M-001 - Worker/outbox correctness is under-specified

`docs/architecture/ARCHITECTURE-SPINE.md:81` binds database leases and idempotency, but it does not bind delivery semantics. Define at-least-once processing, job/outbox states, `not_before`, attempt count, lease owner/expiry, `FOR UPDATE SKIP LOCKED` or equivalent claim rule, retry/backoff, poison-job handling, and the unique consumer idempotency key. Without this, reminder and notification workers can diverge or lose work after a crash.

### M-002 - Material spine decisions lack corresponding ADRs

The spine has twelve adopted decisions but only seven active ADRs. Exact manager-scope representation, durable in-app notification/fan-out, bounded assistant capability, and database-backed asynchronous work are material trade-offs with cross-cutting consequences and should have ADRs. The current ADR set also does not cover the browser/API origin decision identified in H-001.

### M-003 - Technology choices are plausible but not verified or reproducible in the artifacts

The brownfield choice of Python/FastAPI is sound, and React/Next.js/PostgreSQL/Alembic remain current technologies. However:

- `docs/architecture/frontend-architecture.md:5` defers the framework version without binding a Node runtime or starter/toolchain.
- The official registry check found Next.js `16.3.0` requires Node `>=20.9.0`; the repository has no Node runtime declaration or frontend lockfile.
- The official registry check found FastAPI `0.141.1` and Alembic `1.19.1`, while `requirements.txt` uses broad lower bounds and leaves SQLAlchemy/Alembic/PostgreSQL drivers commented out.
- PostgreSQL major version and Chroma persistence-format compatibility are not selected.

Record a verified compatibility envelope and pin reproducible dependencies at implementation kickoff. This does not require binding every patch version in the spine, but local, CI, staging, and production must use compatible runtime/database majors.

### M-004 - The singleton Chroma production topology needs an explicit operational invariant

`docs/architecture/deployment.md:35` constrains the assistant to a singleton API with a persistent local Chroma index, but the deployment remains provider-neutral and does not define volume attachment, replacement rollout, or downtime behavior. State whether the MVP accepts a single-replica/read-write volume with maintenance downtime, or move Chroma behind its own service boundary. Otherwise deployment teams can choose incompatible rollout and persistence models.

### M-005 - Prototype data migration is left as an implementation-time product decision

`docs/architecture/data-architecture.md:123` says submitted demo tickets are migrated "if preservation is required." Decide whether prototype SQLite data is disposable synthetic data or approved migration input. Do not ask a migration story to infer this, especially because the old lifecycle does not map losslessly to the approved four states.

## Good-Spine Rubric Result

| Rubric dimension | Result | Notes |
|---|---|---|
| Real divergence points fixed | **Partial** | Ticket state, snapshot, scope-pair, storage, and Zalo are strong; auth transaction, notification fan-out, onboarding versions, and origin topology remain open. |
| Rules enforce stated prevention | **Partial** | Most AD rules are enforceable. AD-003 claims impossible cross-system atomicity without a protocol; AD-012 lacks delivery semantics. |
| Deferred items are safe | **Fail** | Manager-registry maintenance currently defers authorization freshness. Other explicitly deferred product topics are safe for MVP architecture. |
| Named technology current/verified | **Partial** | Technology families are current, but versions/runtime/database compatibility are absent from the artifacts. |
| Brownfield ratification | **Partial** | The code migration assessment is accurate, but active repository product/docs still contradict the architecture. |
| Product capability coverage | **Partial** | Ticket/auth/Zalo/responsiveness are well covered; onboarding definition lifecycle, admin-created account activation, notification campaigns, and manager-visible data are incomplete. |
| Operational/environmental envelope | **Partial** | Environments, health, migrations, backup, and rollback are present; session origin, worker delivery, and singleton Chroma deployment are unresolved. |

## Blockers Before Architecture Approval

1. Reconcile and approve the durable PRD/product authority (C-001).
2. Define a recoverable registry identity-claim protocol and concrete registry contract (C-002/B-001).
3. Select the OTP provider/environment contract already identified as B-002.
4. Decide the browser/API origin and session/CSRF topology (H-001).
5. Define manager-scope projection freshness or explicitly accept a bounded MVP limitation (H-002).
6. Define targeted-notification aggregate/audience/concurrency contracts (H-003).
7. Define onboarding definition versioning and configuration input (H-004).
8. Resolve contact data ownership and admin-created account activation (H-005).
9. Approve the manager-visible resident data set and complete the corresponding API schemas (H-006).
10. Remediate the potential exposed credential before any external deployment, as already identified in `docs/architecture/implementation-readiness.md`.

## Recommended Verdict

**BLOCKED.** The architecture is a strong draft and can support further design refinement, but the implementation-readiness statement should not permit production stories yet. Once the critical/high findings are resolved, the remaining medium items can be closed as architecture polish or bounded implementation prerequisites without reopening the explicitly deferred product topics.
