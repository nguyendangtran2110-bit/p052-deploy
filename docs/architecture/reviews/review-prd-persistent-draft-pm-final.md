# Final PM Review: Persistent Draft and Rule-Only Zalo

**Reviewer:** John, Product Manager  
**Date:** 2026-08-11  
**Scope:** Closure audit of the four prior PM findings only: draft cardinality/lifecycle, `ZaloLinkPolicy v1`, chatbot field scope/provenance, and quantitative performance deferral.

## Verdict

**PASS.**

The authoritative PRD and architecture now agree on all four reviewed areas. The acceptance criteria are authoritative, internally consistent, and sufficiently testable for implementation planning. No approved deferred area was reopened, and no new product scope was introduced by the fixes.

## Finding Closure

### PMD-001 - Zero-or-one draft cardinality and lifecycle: RESOLVED

The PRD now consistently defines the product invariant as **zero or one active persistent draft per authenticated resident account**:

- [FR-TKT-001](../../PRD.md) uses "at most one";
- Core Data uses "zero or one";
- Section 10 uses "zero or one" and clarifies that the draft is the account's single shared draft only while it exists;
- submission and explicit discard leave the account with no active draft; and
- the architecture spine, domain model, data model, API, diagrams, readiness statement, and [ADR-0004](../adr/ADR-0004-persistent-ticket-draft.md) use the same lifecycle.

The persistence boundary is also explicit and testable: there is no inactivity expiry in MVP; refresh, logout, session expiry, and deactivation do not delete the draft; deactivation blocks access; restoration returns access; permanent account deletion/cleanup is outside MVP.

The immutable `draft_id` generation plus optimistic version prevents a stale request from matching a later draft whose version number repeats. Replace atomically creates a new generation in the same account slot, while submit/discard consume only the expected generation. This supports the product invariant without adding multiple active drafts or draft history.

### PMD-002 - Concrete `ZaloLinkPolicy v1` boundary: RESOLVED

The validation rule is now executable rather than interpretive:

- accepted form: `https://zalo.me/<profile-id>`;
- exact lowercase ASCII host: `zalo.me`;
- exactly one ASCII `[A-Za-z0-9._-]{1,128}` path segment;
- one optional trailing slash normalized away; and
- user-info, ports, queries, fragments, encoded separators, malformed encoding, control characters, and trailing-dot/IDNA host variants rejected.

The PRD, architecture spine, API contract, integration boundary, security contract, and [ADR-0006](../adr/ADR-0006-rule-based-zalo-validation.md) agree. The implementation source is explicitly named as `config/zalo/zalo-link-policy-v1.yaml` with contract fixtures at `tests/fixtures/zalo-link-policy-v1.json`.

The validator stores `validator_version=v1`, reruns on profile edit, and revalidates stale versions before manager handoff. It performs no profile-existence or ownership request and makes no existence, ownership, delivery, or read claim.

The named configuration and fixture files need to be materialized during implementation, but their absence before implementation is not a remaining product or architecture decision.

### PMD-003 - Chatbot field scope and provenance: RESOLVED

[FR-CHAT-002](../../PRD.md) now limits assistant proposals to `Subject`, `Content`, and `Urgency`, derived from the conversation. Resident name, phone, building, floor, and room remain backend-filled read-only data and are never chatbot-owned draft fields.

Proposal provenance is testable:

- the assistant response carries the observed `draft_id`, version, and field fingerprint;
- accepted patches use the normal versioned draft API;
- fields changed after observation become explicit replacement proposals;
- existing resident-entered values cannot be overwritten silently; and
- the assistant cannot submit a ticket or mutate verified profile/location data.

This matches `AD-009`, the assistant API contract, frontend reconciliation behavior, and [ADR-0013](../adr/ADR-0013-bounded-assistant-capability.md).

### PMD-005 - Quantitative performance deferral: RESOLVED

The PRD now states that:

- no quantitative performance criteria are approved for MVP;
- architecture-defined functional, concurrency, recovery, and scoped-list checks still apply; and
- latency, availability, capacity, and quantitative performance targets are deferred post-MVP and are **not an implementation gate** for MVP stories.

Section 10, Implementation Readiness, the architecture spine, deployment architecture, security architecture, and relevant ADRs preserve the same boundary. No deferred KPI or performance target has been converted into a hidden MVP acceptance criterion.

## Deferral and Scope Check

The reviewed changes do not reopen:

- Zalo profile-existence or ownership verification;
- live Zalo messaging or external delivery tracking;
- chatbot source governance;
- KPI or quantitative performance targets; or
- any other Section 10 post-MVP item.

The added draft generation, concurrency, idempotency, provenance, and local Zalo-policy mechanics are necessary implementation controls for the approved behaviors. They do not add a new resident or manager capability.

## Focused Readiness Decision

The PM gate for these two product changes is **PASS**. Stories may treat the following as stable product inputs:

1. an authenticated resident account has zero or one active persistent ticket draft;
2. the one draft is shared across sessions/devices while active and follows the approved no-expiry/deactivation lifecycle;
3. assistant participation is limited to provenance-bound subject/content/urgency proposals;
4. Zalo validation follows `ZaloLinkPolicy v1` locally with no external verification; and
5. quantitative performance targets remain deferred and do not block MVP stories.

Repository-wide implementation dependencies and deployment/security concerns remain governed by [implementation-readiness.md](../implementation-readiness.md); they are outside this focused PM closure review.
