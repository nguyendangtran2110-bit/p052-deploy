# Persistent Draft UX and Frontend/API Seam Review

**Reviewer:** Sally, UX Designer  
**Scope:** Persistent account-owned ticket draft, manual/assistant sharing, session and device continuity, conflict recovery, submission ambiguity, mobile-first accessibility, and Zalo fallback language.  
**Verdict:** **PASS WITH CONCERNS.** The architecture now has a coherent single-draft source of truth and resolves the earlier cross-session/idempotency gaps. The findings below do not require a different storage architecture, but UX-001 through UX-004 must be made explicit before persistent-draft frontend stories are accepted.

## Findings

### IMPORTANT

#### UX-001 - “Existing draft” prompts have no precise trigger boundary

The architecture says an `existing` start outcome presents `Resume draft` or `Discard and start new`, while route navigation, refresh, login, and device changes reload the same draft ([frontend-architecture.md](../frontend-architecture.md), Persistent Ticket Draft and Start, resume, and replace; [api-contracts.md](../api-contracts.md), Persistent ticket draft contract). It does not distinguish:

- explicitly choosing `Create new ticket`;
- returning directly to the draft editor;
- refreshing the editor;
- following a deep link to the editor after login; or
- an assistant detecting ticket intent while an existing draft already exists.

If every `existing` response opens the choice dialog, residents are repeatedly asked whether to discard work merely by resuming it. If the assistant calls `start` and applies its patch immediately, it can modify an unrelated saved ticket before the resident chooses.

**Required UX/API rule:** direct entry to the active draft editor resumes without a replace prompt. The choice dialog appears only after an explicit new-ticket intent. An assistant proposal must not mutate an existing draft until the resident chooses `Resume draft` or confirms `Discard and start new`. Replacement must use the single atomic `replace` endpoint, never `discard` followed by `start`.

#### UX-002 - Save serialization and durability semantics are still underspecified

The frontend owns an in-memory edit buffer and shows `saving`, `saved`, `offline/unavailable`, and `conflict`, but neither the frontend contract nor API contract specifies whether saves occur on blur, debounce, explicit action, or navigation ([frontend-architecture.md](../frontend-architecture.md), Persistent Ticket Draft; [data-architecture.md](../data-architecture.md), Frontend edit buffer). Multiple rapid patches can leave with the same `expected_version`, creating self-conflicts; responses can return out of order; and “flush where possible” does not define whether internal navigation waits or proceeds.

**Required frontend contract:** use a single-flight/coalescing save queue per draft. Only one mutation is in flight; accepted responses advance the baseline/version; later buffered edits are rebased visibly and sent next. `Saved` means the API accepted the exact currently displayed values, not merely that a request was sent. Internal OnBxrd navigation should await or cancel-confirm an unsaved save; hard refresh/tab close may warn but must not promise asynchronous persistence. Offline copy must state that only the last saved server version is available on another device.

#### UX-003 - Concurrent conflict recovery lacks a field-level apply contract

On `ticket_draft_conflict`, the UI preserves attempted changes and offers `Use latest saved draft` or `Review and apply my changes` ([frontend-architecture.md](../frontend-architecture.md), Concurrent editing). The contract correctly forbids silent merge, but “review and apply” is not defined. Subject, content, and urgency can each differ, and sending a full stale local object as one patch could overwrite fields accepted by the other session.

**Required UX/API rule:** present a mobile-friendly per-field comparison against the returned server draft, default each conflict to the latest saved value, and let the resident explicitly choose which local field values to apply. Build the next patch only from chosen fields against the returned current version. If another conflict occurs, repeat the review; never auto-force or provide a blanket “overwrite latest” action. Preserve unsent local text until the resident resolves or intentionally discards it.

#### UX-004 - Assistant patches need draft-version provenance

The assistant returns a patch, and the frontend later applies accepted fields through the versioned draft API ([api-contracts.md](../api-contracts.md), Assistant Surface). The assistant request/response does not identify the draft version or field baseline used to produce the proposal. While an LLM request is running, a manual form or another device may update the draft. A field that was empty when the assistant started may no longer be empty when its answer returns.

**Required contract:** include the observed draft version or field fingerprint with assistant proposal context and return it with the proposal. Before applying, compare with the latest fetched draft. Fields that are no longer unchanged/empty become explicit replacement proposals; they are never auto-applied. The assistant-unavailable path leaves the manual draft fully usable and does not strand a `saving` state.

#### UX-005 - Session-expiry buffer ownership is not fully enforceable

The server draft correctly survives logout/login and device changes, and account switch purges client caches ([authentication-authorization.md](../authentication-authorization.md), Draft Authorization; [security.md](../security.md), Sensitive Data Handling). However, the accessibility matrix says session expiry moves to login while retaining the unsaved buffer “only in the current page.” A route to login can unmount that page, and a different account can authenticate in the same tab.

**Required frontend rule:** bind the unsaved buffer to the last server-confirmed account ID plus `session_epoch` in memory above the public/authenticated route boundary. After login, call `/auth/me` before rendering or reapplying it. Preserve it only for the same account; purge it before any different account's draft or identity renders. If the page reloads during expiry, only the last server-saved draft is recoverable, and the login copy must not promise otherwise.

#### UX-006 - Submission ambiguity is strong, but key lifecycle and waiting UX need closure

The submission status endpoint and atomic submit/delete transaction resolve the primary duplicate-ticket risk ([api-contracts.md](../api-contracts.md), Persistent ticket draft contract). Remaining ambiguity exists around:

- generating a new key after a definitive validation failure and subsequent edit;
- retaining the key long enough for `202 submission_processing` polling;
- preventing route/account changes while an outcome is unknown; and
- handling a status lookup that remains unavailable.

**Required frontend/API rule:** one submission key is bound to one submitted draft version/fingerprint. Reuse it only for retry or status resolution of that exact attempt. After a definitive validation failure and any edit, generate a new key. Keep the resident on a non-editable, accessible pending-result state while `202` continues; allow safe navigation only with a persistent way to resume status resolution. Define the minimum server idempotency/status retention window and bounded polling/backoff behavior.

### OPTIONAL / UX SPECIFICATION

#### UX-007 - Mobile and screen-reader behavior needs component-level acceptance cases

The WCAG 2.2 AA interaction matrix is a good architecture baseline, but the persistent-draft experience needs testable mobile patterns:

- At 360px, resume/replace and discard confirmations must keep the safe action visible and avoid side-by-side comparison layouts.
- Save-status announcements must be debounced; announcing `saving`/`saved` on every keystroke will overwhelm screen-reader users.
- `Offline/unavailable` and conflict states must be adjacent to the affected form and remain understandable without color.
- The conflict review must preserve long Vietnamese content, keyboard position, and focus when applying selected fields.
- Replacement/discard confirmation must name the destructive result and return focus predictably on cancel.

These belong in the UX specification and acceptance tests rather than a new architectural decision.

## Zalo Fallback Review

**PASS.** The architecture consistently states that validation is local and structural only, performs no profile-existence request, and makes no ownership or delivery claim ([integrations.md](../integrations.md), Zalo; [frontend-architecture.md](../frontend-architecture.md), Ticket Detail and Interaction matrix; [ADR-0006](../adr/ADR-0006-rule-based-zalo-validation.md)).

Recommended Vietnamese intent for the fallback copy:

> OnBxrd không có đường dẫn Zalo hợp lệ để mở cho cư dân này. Bạn có thể dùng Notify để gửi thông báo trong OnBxrd.

Avoid wording such as “Zalo profile does not exist,” “account not found,” or “Zalo verification failed,” because OnBxrd does not test existence.

## Confirmed Strengths

- Exactly one server-owned draft exists per authenticated resident account.
- Logout, login, browser, and device changes preserve the saved draft without exposing it to another account.
- Resume is the safe default and replacement resets the existing row atomically.
- Draft updates, replacement, discard, and submission use optimistic versions and idempotency.
- Submission creates the immutable ticket and removes the draft in one transaction.
- Manual and assistant paths share the same draft API; the assistant cannot submit or mutate verified resident/location data.
- Unsaved browser state is explicitly non-authoritative and never stored in browser persistence.

## UX Artifacts Required Before Draft Frontend Acceptance

1. New-ticket intent versus direct-resume route/state diagram, including assistant entry.
2. Autosave queue and save-status state machine.
3. Field-level concurrent-conflict reconciliation wireflow at 360px and desktop widths.
4. Session-expiry/same-account/different-account transition flow.
5. Submission pending/ambiguous/failure recovery flow.
6. Accessible Vietnamese copy matrix for resume, replace, discard, offline, conflict, and pending submission states.

