# PM Review: Rule-Only Zalo and Persistent Ticket Draft

**Reviewer:** John, Product Manager  
**Date:** 2026-08-11  
**Scope:** The two requested PRD changes only: local rule-based Zalo validation with existence/ownership verification deferred, and one persistent active ticket draft per authenticated resident account.

## Verdict

**BLOCKED pending narrow PRD corrections.**

The architecture is internally coherent around both changes. It consistently implements local-only Zalo validation and a server-owned, account-unique ticket draft with optimistic concurrency and atomic submission. The PRD is now marked final and authoritative, with no proposed acceptance criteria remaining.

However, the authoritative PRD still contains a contradictory draft-cardinality statement, an untestable Zalo allowlist boundary, and two smaller inconsistencies that would force implementation or test agents to invent behavior. These are narrow corrections; they do not require reopening the wider MVP scope.

## BLOCKING Findings

### PMD-001 - The PRD says both "at most one" and "exactly one" active draft

[FR-TKT-001](../../PRD.md) says an authenticated account has **at most one** active draft. The user journeys, submission criteria, and architecture also allow zero active drafts:

- the draft is created only when ticket creation starts;
- `GET /resident/ticket-draft` may return `204`;
- explicit discard deletes the draft; and
- successful submission deletes the draft atomically.

Section 10 instead says every authenticated resident account has **exactly one** persistent active draft. Taken literally, that requires a draft to exist immediately after registration and to be recreated immediately after discard or submission, contradicting the rest of the product and architecture.

The intended invariant appears to be:

> An authenticated resident account may have zero or one active ticket draft. While an active draft exists, it is the account's single persistent draft shared across sessions and devices.

**Required correction:** use one cardinality statement consistently in the terminology, FR-TKT-001, data requirements, Section 10, architecture readiness, and ADR context. Do not use "exactly one" unless the product truly requires an always-present draft.

### PMD-002 - The rule-based Zalo acceptance boundary is not concrete enough to test

The product and architecture correctly agree that MVP validation is structural and makes no external existence or ownership request. The remaining gap is that both use "approved Zalo hosts and profile-link patterns" without identifying the approved allowlist or a versioned configuration artifact that owns it ([FR-TKT-006](../../PRD.md); [integrations.md](../integrations.md), Zalo Validation Boundary).

An implementation agent must otherwise invent which hosts, subdomains, path shapes, query parameters, and canonical forms are accepted. A test agent cannot determine whether a syntactically valid but unsupported Zalo URL should pass.

**Required correction:** bind validation to a named, version-controlled allowlist/configuration with approved MVP entries and fixtures. The PRD can remain product-level, but the architecture/test contract must identify the exact source of truth. This does not require Zalo API access and does not reopen profile-existence verification.

## IMPORTANT Findings

### PMD-003 - Chatbot draft criteria ambiguously reintroduce verified profile fields

[FR-CHAT-002](../../PRD.md) says empty draft fields may be filled from the conversation **or verified profile**. The approved persistent draft schema contains only `subject`, `content`, and `urgency`; resident name, phone, building, floor, and room remain read-only profile data and are snapshotted only on submission.

This wording could lead an implementation agent to copy profile fields into the persistent draft or let the chatbot manipulate them, contradicting FR-TKT-001 and the architecture.

**Required correction:** state that the chatbot may propose only subject, content, and urgency. Verified resident/location data is displayed read-only and is never a chatbot-owned draft field.

### PMD-004 - Persistent-draft expiry and account-lifecycle behavior are implicit

The architecture says a draft persists until submission, discard/replacement, or account lifecycle cleanup, but it does not define inactivity expiry or what cleanup means. For a persistent sensitive record, implementation agents could reasonably choose incompatible behaviors such as indefinite retention, automatic expiry, deletion on deactivation, or restoration with the account.

**Required correction:** make the MVP rule explicit. The smallest consistent rule is no inactivity expiry in MVP; logout/session expiry does not delete the draft; deactivation makes it inaccessible; final account deletion/cleanup remains governed by the account lifecycle policy. If a different rule is intended, it needs an acceptance criterion.

### PMD-005 - A closed performance deferral is reopened by the NFR section

Section 10 and Implementation Readiness correctly say quantitative performance targets are deferred and are not MVP blockers. The Performance section nevertheless says those targets "must be approved before performance-sensitive stories pass the implementation gate."

That sentence turns the approved deferral back into an implementation blocker and makes the PRD lifecycle internally inconsistent.

**Required correction:** state that MVP stories use architecture-defined functional/reliability checks without quantitative product thresholds; quantitative targets remain post-MVP unless separately brought back into scope.

## Acceptance-Criteria Assessment

### Rule-based Zalo validation

Once the exact allowlist source is bound, the criteria are authoritative and testable:

- accepted scheme/host/path fixtures normalize successfully;
- unsupported schemes, hosts, ports, credentials, malformed encodings, and executable forms fail locally;
- no Zalo or other existence/ownership HTTP call occurs;
- editing a link reruns the same validation;
- missing/invalid links retain the `Zalo` fallback affordance;
- managers receive no existence, ownership, sent, delivered, or read claim; and
- profile-existence and ownership verification remain deferred.

### Persistent account draft

After the cardinality and lifecycle wording is corrected, the criteria are authoritative and testable:

- an authenticated resident with no draft can start one;
- concurrent starts return the same account-owned row;
- manual and chatbot flows read/update that same row;
- logout/login and another authenticated device load the saved draft;
- anonymous users and other roles cannot create or access it;
- expected-version updates prevent silent overwrites;
- replacement resets the one row after confirmation;
- discard leaves the account with no active draft;
- submit creates one ticket and deletes the draft in the same transaction;
- repeated submission returns the original result; and
- a stale save cannot recreate a submitted or discarded draft.

## Architecture Alignment

The architecture is aligned with the intended **zero-or-one active draft** interpretation:

- [ARCHITECTURE-SPINE.md](../ARCHITECTURE-SPINE.md) uses "at most one" and makes PostgreSQL authoritative.
- [ADR-0004](../adr/ADR-0004-persistent-ticket-draft.md) defines one unique account row, cross-session/device continuity, optimistic concurrency, and atomic submit/delete.
- [data-architecture.md](../data-architecture.md) defines the unique account constraint and prevents stale mutations from recreating a row.
- [api-contracts.md](../api-contracts.md) covers start, read, update, replace, discard, submit, conflict, and ambiguous submission outcomes.
- [frontend-architecture.md](../frontend-architecture.md) keeps persistent draft fields out of browser storage and defines resume/replace/conflict UX.

The architecture is also aligned with rule-only Zalo validation:

- [ARCHITECTURE-SPINE.md](../ARCHITECTURE-SPINE.md) rejects external existence checks.
- [ADR-0006](../adr/ADR-0006-rule-based-zalo-validation.md) makes local parsing/allowlisting the only MVP validation.
- [integrations.md](../integrations.md) treats Zalo as browser navigation rather than an API integration.

No stale session-only draft ADR remains in the active architecture set. Older review files describe pre-resolution findings but are explicitly historical evidence through [review-resolution.md](review-resolution.md).

## Deferral and Scope-Creep Audit

**Deferral result:** Zalo existence/ownership verification remains cleanly deferred. No external Zalo SDK, remote profile lookup, ownership proof, delivery tracking, or live messaging has been reintroduced.

**Scope result:** the database row, uniqueness constraint, optimistic versioning, idempotency, conflict response, and atomic submit/delete behavior are necessary consequences of a persistent draft shared across sessions/devices. They are not scope creep. The design does not introduce multiple drafts, draft history, anonymous drafts, manager/admin draft access, attachments, categories, or background Zalo verification.

The performance-target sentence noted in PMD-005 is the only reviewed text that reopens an explicitly approved deferral.

## Exit Criteria

This focused review can move to **PASS** when:

1. "exactly one" is reconciled with the zero-or-one lifecycle;
2. the exact Zalo validation allowlist source is named and versioned;
3. FR-CHAT-002 limits chatbot draft fields to subject/content/urgency;
4. persistent-draft expiry/account-lifecycle behavior is explicit; and
5. quantitative performance targets remain unambiguously deferred.

No broader product area needs to be reopened to make these corrections.
