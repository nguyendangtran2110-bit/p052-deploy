# PM Alignment Review

**Reviewer:** John, Product Manager  
**Date:** 2026-08-11  
**Scope:** OnBxrd MVP architecture set, with emphasis on `ARCHITECTURE-SPINE.md`, reviewed against `docs/PRD.md`, the latest approved Party Mode decisions, repository governance, and the current brownfield implementation.

## Verdict

**BLOCKED for implementation handoff.**

The architecture direction is substantially aligned with the latest approved MVP intent. The ticket lifecycle, transient ticket workspace, manager scope, historical ticket access, Zalo boundary, registration model, and desktop-layout/accessibility baseline are represented clearly and concretely.

The blocking problem is not the architecture's core shape. It is that the architecture currently contradicts higher-authority product artifacts and leaves several approved product behaviors without executable contracts. Under `AGENTS.md`, implementation agents must follow the approved PRD before architecture. They therefore cannot safely treat this architecture as authoritative until the product sources are reconciled.

## BLOCKING Findings

### PM-001 - Product authority is split across mutually contradictory artifacts

The architecture correctly follows the latest user decisions, but the referenced PRD explicitly says it is a non-authoritative working draft ([PRD](../../PRD.md), Draft Authority and Implementation Readiness). It still contains superseded requirements, including:

- Zalo profile-existence verification;
- ticket viewing not changing status;
- persistent ticket drafts across authenticated sessions;
- a completion note for `Resolved`;
- unresolved authentication, ticket, Zalo, and frontend-layout decisions that the user has since approved.

The repository-level [PRODUCT.md](../../../PRODUCT.md) also still specifies the old `DRAFT -> SUBMITTED -> APPROVED -> IN_PROGRESS -> RESOLVED` lifecycle, a Zalo OA/group workflow, one-building scope, resolution notes, and PostgreSQL with pgvector. Those are incompatible with the architecture's four-state lifecycle, outbound-only personal Zalo link, multi-building manager scope, no resolved note, and retained Chroma boundary.

The architecture README identifies old API/deployment documents as superseded but does not identify `PRODUCT.md` as stale, and it still calls the draft PRD a source. This forces implementation agents to choose which authority to violate.

**Required resolution:** update and approve the PRD with the latest decisions, reconcile or explicitly supersede `PRODUCT.md`, and update the architecture authority map. This is required before any production story is implementation-ready.

### PM-002 - Approved resident and manager profile-edit behavior is incomplete

The approved product rule is:

- resident ID, manager ID, and username are immutable;
- building/floor/room and manager assignments are administrator-controlled;
- residents and managers may edit their other ordinary profile fields, including name, phone, email, and password.

The architecture exposes only `PATCH /resident/profile` for unspecified contact/preference fields. It exposes no manager profile update, no authenticated password-change surface, and no contract for what happens when an owner changes phone or email that was originally matched to the registry ([api-contracts.md](../api-contracts.md), Resident and Manager Surfaces; [authentication-authorization.md](../authentication-authorization.md), Login, Logout, and Recovery).

Implementation agents would have to invent whether contact changes require password confirmation, OTP reverification, registry matching, session revocation, or recovery-channel replacement.

**Required resolution:** add a field-level editability matrix and API/security contract for resident and manager profile updates and password changes. Keep location and scope outside owner-editable payloads.

### PM-003 - Administrator-created account activation has no product or API contract

The user approved administrator creation of resident and manager accounts. The architecture names `POST /admin/accounts/residents` and `POST /admin/accounts/managers`, but does not define:

- who chooses the username and initial password;
- whether the account starts active or pending activation;
- whether registry-contact OTP is still required;
- how credentials or an activation action reach the user;
- how an existing claimed ID or username conflict is handled; or
- whether administrator creation creates the registry claim immediately.

This is distinct from public self-registration and cannot be inferred safely from it. It affects account security, UX, and persistent account state.

**Required resolution:** approve one administrator-created-account activation path and add its request, state-transition, idempotency, and error contract before administrator account stories begin.

### PM-004 - Manager scope freshness is security-critical but undefined

The architecture says grants are imported during manager registration, current grants authorize historical tickets, revoked grants remove access, and scope projection changes are audited. The registry contract, however, defines lookup and claim only; no refresh, synchronization, version-check, or administrator correction path for manager grants exists ([integrations.md](../integrations.md), Registry; [authentication-authorization.md](../authentication-authorization.md), Manager Scope Enforcement).

Deferring manager-registry maintenance is valid, but it does not answer when OnBxrd stops trusting a stale authorization projection. The current documents simultaneously defer the mechanism and promise effective revocation after an unspecified update is applied.

**Required resolution:** the Architect must choose and document a bounded MVP freshness rule that does not reopen the maintenance workflow, such as version checking at login/session renewal plus an explicit operational refresh contract. Authorization stories cannot safely invent this behavior.

## IMPORTANT Findings

### PM-005 - Concurrent full-detail opens do not produce the approved loser notification

Opening full detail is itself the `PENDING -> RESOLVING` state mutation. The approved rule says that when two managers attempt conflicting state changes, the first accepted change wins and the other manager receives an OnBxrd notification.

The current open command treats an already `RESOLVING` ticket as an ordinary idempotent success. It does not distinguish a concurrent losing open from a later legitimate view and does not create a conflict notification ([api-contracts.md](../api-contracts.md), Open Detail Command; [ADR-0005](../adr/ADR-0005-ticket-concurrency-and-snapshots.md)).

**Required change:** define compare-and-swap behavior for `PENDING -> RESOLVING`, including how the API identifies and notifies a concurrent loser without notifying every manager who opens an already-resolving ticket later.

### PM-006 - Targeted notification audience contracts are missing

The MVP product already fixes the important audience behavior: managers can target assigned building scope, floor, room/unit, or selected in-scope residents; some managers have per-building `ALL_FLOORS`; preview and send must not expand scope; `Notify` is resident-preselected from ticket detail.

The API lists preview/send endpoints but provides no audience request schema, preview token/version, resolved-recipient response, or stale-preview semantics. These are authorization and UX contracts, not the explicitly deferred notification type catalog or retention policy.

**Required change:** specify the MVP audience selector contract and preview/send revalidation contract while leaving the broader type catalog and retention deferred.

### PM-007 - Configurable onboarding lacks a configuration and version-change contract

The PRD requires onboarding steps to evolve as surveillance/research continues. The architecture stores versioned definitions and progress but does not decide how MVP definitions enter the system or what happens when steps are added, reordered, made optional, or retired.

This does not require a new administrator UI. A seed/configuration/import path is sufficient for MVP, but implementation agents must not invent whether existing residents inherit new required steps or lose prior completion.

**Required change:** define the MVP definition source and progress migration invariants. Keep document upload deferred.

## Scope-Creep and Deferral Audit

The architecture appropriately keeps these topics deferred and does not treat them as blockers: benefit governance, chatbot source governance, notification type catalog and retention, manager-registry maintenance workflow ownership, KPI targets, and quantitative performance targets.

The following technical decisions are justified implementation architecture, not product scope creep:

- modular monolith rather than microservices;
- PostgreSQL transactions and optimistic concurrency;
- a database outbox/worker for reminders and notification fan-out;
- opaque sessions, CSRF protection, and Argon2id;
- `sessionStorage` for the ticket workspace;
- adapter boundaries for registry, OTP, LLM, knowledge, and Zalo.

One boundary needs tightening: auditing notification read changes "where required" is undefined while notification retention is deferred. Do not introduce an indefinite per-read audit history unless a concrete security or acceptance requirement calls for it.

## Stable Product Invariants Confirmed

The following architecture inputs match the approved MVP intent and should remain stable:

- resident and manager self-registration requires an active registry identity, matching contact, and OTP verification;
- administrators have no public registration path;
- resident location and manager scope are derived from registry identity and are not owner-editable;
- manager authorization uses exact building-floor pairs or per-building `ALL_FLOORS`;
- all currently in-scope managers may access matching historical tickets;
- ticket submission snapshots resident name, phone, building, floor, and room;
- no persistent server ticket draft exists;
- subject, content, and urgency use one shared client workspace across manual/chat flows;
- urgency values are `LOW`, `NORMAL`, and `HIGH`, with `NORMAL` as the product default;
- full ticket detail changes `PENDING` to `RESOLVING`;
- `RESOLVED` and `DENIED` are terminal, both require confirmation, and only `DENIED` requires explanation;
- first-valid-write-wins protects terminal transitions;
- `Zalo` performs rule-validated outbound profile navigation only;
- missing/invalid Zalo uses the `Notify` fallback from ticket detail;
- notifications persist a type and read/unread state;
- WCAG 2.2 AA is binding;
- resident and manager flows are desktop-first from a 1024 CSS px minimum product viewport; mobile and tablet UX/UI are out of scope while WCAG desktop zoom/reflow remains binding.

## Brownfield Technology Reality Check

- FastAPI, Python 3.11, LangGraph, LlamaIndex/Chroma, Docker, and GitHub Actions are real repository baselines. Preserving them behind cleaner boundaries is credible.
- No frontend project currently exists. Next.js/React is consistent with repository intent and older project documentation, but it is new scaffolding rather than reused implementation.
- PostgreSQL/Alembic is a justified migration for the approved data and concurrency rules, but the current application still defaults to SQLite and the SQLAlchemy/Alembic/PostgreSQL dependencies are commented out. Estimates and stories must treat this as a database-platform migration, not a configuration flip.
- Retaining Chroma matches the actual RAG implementation. The conflicting pgvector statement in `PRODUCT.md` must be removed or superseded rather than silently ignored.

## PM Exit Criteria

The PM alignment gate can move from `BLOCKED` to `PASS WITH CONCERNS` when:

1. the PRD and `PRODUCT.md` are reconciled with the approved MVP decisions;
2. profile editing and administrator-created account activation are specified;
3. manager-scope freshness has a bounded architecture rule;
4. concurrent open-detail conflict behavior is explicit; and
5. notification audience and onboarding-definition contracts are added.

The external registry contract, OTP provider, and credential remediation remain legitimate implementation blockers already identified by the architecture review set.
