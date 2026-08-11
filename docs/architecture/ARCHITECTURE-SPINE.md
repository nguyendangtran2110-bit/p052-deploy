---
status: final
updated: 2026-08-11
---

# OnBxrd MVP Architecture Spine

This is the implementation consistency contract. It fixes cross-module invariants and intentionally defers structural detail that compliant code can choose independently.

## Paradigm

Use a modular monolith with explicit domain modules behind one FastAPI process, one relational source of truth, and a separately scheduled worker process built from the same backend package. The web client is a separate React/Next.js application. Modules communicate through application services and typed contracts; they do not import another module's persistence implementation.

## Adopted Decisions

### AD-001 - Modular monolith and dependency direction [ADOPTED]

- **Binds:** Web/API, domain services, integration adapters, worker, and persistence boundaries.
- **Prevents:** Feature teams creating incompatible service boundaries or direct cross-module table writes.
- **Rule:** Routes call application services; application services own domain mutations; repositories own persistence; adapters own external systems. Dependencies point inward toward domain contracts.

### AD-002 - PostgreSQL system of record [ADOPTED]

- **Binds:** Accounts, registry claims, manager scope, onboarding, benefits, tickets, events, notifications, and audits.
- **Prevents:** SQLite demo state, browser state, Chroma, or external systems becoming authoritative business state.
- **Rule:** PostgreSQL is authoritative for product data. SQLite remains only as a local migration aid and is not a production deployment target.

### AD-003 - Registry-backed identity [ADOPTED]

- **Binds:** Resident/manager registration and account-to-building associations.
- **Prevents:** An ID-only public signup from creating an unbound or out-of-scope account.
- **Rule:** Registration matches an active registry record, verifies a matching contact through OTP, then atomically creates the account and unique OnBxrd claim in PostgreSQL. The registry is read-only in MVP; location/scope and source version are projected from it. Administrator accounts are provisioned out of band, while administrator-created resident/manager accounts use pending activation and the same verification invariant.

### AD-004 - Exact manager scope pairs [ADOPTED]

- **Binds:** Every manager read, ticket action, resident contact, onboarding view, and notification audience.
- **Prevents:** Combining an allowed-building list with an independent allowed-floor list.
- **Rule:** A manager grant is `(building_id, floor_id)` or `(building_id, ALL_FLOORS)`. Authorization evaluates the pair against the resource's current or immutable snapshot scope.

### AD-005 - Immutable ticket location snapshots [ADOPTED]

- **Binds:** Ticket history, resident moves, manager queue visibility, and audit reconstruction.
- **Prevents:** A resident move rewriting historical responsibility or making an old ticket disappear from the resident's history.
- **Rule:** Submission snapshots resident name, phone, building number, floor, and room. The submitted snapshot never changes. Manager access to historical tickets uses the snapshot scope; current resident profile data is separate.

### AD-006 - Single persistent account ticket draft [ADOPTED]

- **Binds:** Chat/form handoff and draft persistence semantics.
- **Prevents:** Multiple active drafts, browser/device-specific divergence, cross-account disclosure, and last-write-wins corruption.
- **Rule:** PostgreSQL stores zero or one active draft per authenticated resident account, shared by manual and assistant flows across sessions/devices. Each draft generation has an immutable `draft_id`; mutations compare account, `draft_id`, and expected version and use an idempotency key. Replace creates a new generation atomically in the same account slot. Submission creates the ticket, durable account/key result, and draft deletion atomically. Anonymous users have no persistent draft.

### AD-007 - Command-based ticket state mutation [ADOPTED]

- **Binds:** Automatic `Resolving`, terminal confirmation, status history, and concurrent manager actions.
- **Prevents:** Side effects hidden in cache reads or last-write-wins status corruption.
- **Rule:** Full detail opening sends the observed status/version and an attempt key. The first `Pending` to `Resolving` compare-and-swap wins; a concurrent stale opener receives a conflict result and one notification, while a later view that observed current `Resolving` is a normal read. Terminal transitions require the expected ticket version. The first valid transaction wins; stale managers receive one conflict notification.

### AD-008 - In-app notification record [ADOPTED]

- **Binds:** Resident/manager notification history, conflict notifications, `Notify`, and unread state.
- **Prevents:** Contact actions that cannot be audited or messages that exist only as transient browser UI.
- **Rule:** Manager-authored sends persist a campaign, authorized audience selector, preview recipient hash, scope version, and per-recipient notifications. Send re-resolves the audience and fails stale rather than expanding it. Notifications store recipient, extensible type, payload, read timestamp, and source event. External delivery is not an MVP dependency.

### AD-009 - Bounded assistant capability [ADOPTED]

- **Binds:** Chatbot retrieval, ticket-field extraction, and resident control.
- **Prevents:** The model mutating verified profile data, submitting tickets, or answering outside approved building information.
- **Rule:** The assistant may return grounded answers and patches for subject/content/urgency only. The backend fills resident/location fields and the resident submits the ticket.

### AD-010 - Rule-based Zalo validation [ADOPTED]

- **Binds:** Resident profile input and manager `Zalo` action.
- **Prevents:** SSRF-like profile checks, unsupported provider assumptions, and false delivery claims.
- **Rule:** Apply version-controlled `ZaloLinkPolicy v1` locally: HTTPS, exact `zalo.me` host, one approved profile-ID path segment, and no unsafe URL components. Store the normalized URL with validator version and revalidate stale versions before an authorized manager handoff. Do not call Zalo or claim ownership, existence, delivery, or read state.

### AD-011 - Role-specific responsive web shells [ADOPTED]

- **Binds:** Route ownership, state ownership, and accessibility baseline.
- **Prevents:** Manager-only assumptions leaking into resident mobile flows or client-side role checks becoming authorization.
- **Rule:** Resident routes are mobile-first; manager routes are desktop-first and responsive; all conform to WCAG 2.2 AA. The backend remains the authority for role and scope.

### AD-012 - Database-backed asynchronous work [ADOPTED]

- **Binds:** Automated onboarding reminders, OTP expiry/cleanup, and notification fan-out.
- **Prevents:** Timers tied to one API process or duplicate scheduled actions after restarts.
- **Rule:** API mutations commit an outbox/job record in the same PostgreSQL transaction as the source event. Workers process jobs at least once using lease owner/expiry, `not_before`, bounded retry/backoff, dead-letter state, and unique consumer idempotency keys.

### AD-013 - Same-origin browser/API boundary [ADOPTED]

- **Binds:** Web deployment, session cookies, CSRF, CORS, local development, and API routing.
- **Prevents:** Frontend and backend choosing incompatible cookie domains or credentialed cross-origin behavior.
- **Rule:** One public origin serves the web application and reverse-proxies `/api/*` to FastAPI. Production browser calls are same-origin; credentialed CORS is disabled. Authenticated mutations use a session-bound synchronizer CSRF token plus Origin validation.

### AD-014 - Bounded manager-scope freshness [ADOPTED]

- **Binds:** Manager sessions, registry projections, scope revocation, reads, ticket actions, Zalo, and notification sends.
- **Prevents:** A removed grant remaining effective indefinitely or every module inventing its own refresh rule.
- **Rule:** Refresh the registry projection at login, session renewal, and before every scoped mutation. Scope-sensitive reads require a projection checked within the configured security window. When refresh is required and the registry is unavailable, fail closed; a changed projection increments the local scope version, is audited, and invalidates protected caches/session scope immediately.

### AD-015 - Versioned onboarding definitions [ADOPTED]

- **Binds:** Onboarding configuration, resident enrollment, progress history, and reminder calculation.
- **Prevents:** Deployments silently resetting progress or assigning different requirements to equivalent residents.
- **Rule:** Version-controlled seed files publish immutable building-scoped definition versions. Each resident is pinned to one version. Existing enrollments change only through an explicit audited migration that carries completion by stable step key and recalculates reminders.

### AD-016 - Verified contact ownership [ADOPTED]

- **Binds:** Profile edits, recovery, ticket snapshots, registry matching, and administrator corrections.
- **Prevents:** Registry snapshots, recovery factors, and editable display data drifting without an authority rule.
- **Rule:** Registry contacts are read-only verification evidence. The account owns current verified phone/email and password; profile owns editable display name and preferences. Username, registry ID, resident location, and manager grants are owner-immutable. Contact replacement requires OTP verification; password replacement requires recent authentication and revokes other sessions.

### AD-017 - Constrained Chroma runtime [ADOPTED]

- **Binds:** Assistant deployment, index replacement, scaling, and outage behavior.
- **Prevents:** Multiple writers corrupting a local index or deployment teams treating Chroma as irreplaceable product state.
- **Rule:** MVP serves a versioned Chroma index read-only from one assistant-serving API replica. Index replacement is validated before an explicit maintenance switch. Assistant unavailability does not block manual ticket creation or other product domains.

## Inherited Brownfield Constraints

- Keep the existing Python 3.11/FastAPI service as the backend starting point.
- Preserve the existing LangGraph and LlamaIndex/Chroma boundaries behind adapters while the chatbot is migrated from demo behavior.
- Preserve Docker multi-stage builds and GitHub Actions as the delivery baseline.
- Treat current demo routes, SQLite ticket tables, HITL statuses, and hard-coded profile data as migration targets, not contracts.

## Deferred

The architecture does not decide benefit governance, chatbot source governance, notification type catalog/retention, manager-registry maintenance ownership/workflow, KPI targets, performance targets, document uploads, external notification channels, live Zalo messaging/profile-existence verification, or advanced administrator content access. Runtime registry consumption and scope freshness are not deferred because authentication and authorization depend on them.
