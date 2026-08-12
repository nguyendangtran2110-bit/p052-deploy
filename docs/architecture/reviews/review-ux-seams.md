# UX Architecture Seam Review

**Reviewer:** Sally, UX Designer  
**Review scope:** MVP architecture documents and ADRs, with emphasis on architecture-sensitive flows and frontend/backend seams.  
**Verdict:** **BLOCKED for implementation stories that touch ticket mutation, ticket submission, notification contact, session recovery, or administrator provisioning.** The desktop-layout and accessibility baseline is directionally strong, but several contracts still allow two compliant implementations to produce different user-visible behavior.

## Findings

### BLOCKING

#### UX-001 - Concurrent full-detail opens do not implement the approved loser notification

`POST /manager/tickets/{id}/open` is defined as idempotent: if the ticket is already `RESOLVING`, it returns the current detail without a transition ([api-contracts.md](../api-contracts.md), Open detail command; [domain-model.md](../domain-model.md), Ticket State Machine). The approved behavior says that when managers change state concurrently, the first accepted change wins and the other manager receives a notification. Opening full detail is itself the `PENDING -> RESOLVING` state change, so two managers opening at once need a defined winner/loser result. As written, the second manager can receive a successful 200 with no indication that its open lost and no conflict notification.

**Required architectural clarification:** make the open command compare-and-swap `PENDING` with the observed version and return an explicit `opened_by_other_manager`/conflict result plus an idempotent notification to the second manager, or explicitly state that open-open races are exempt from conflict notifications. The UI needs the result shape, announcement text, and whether the detail remains visible.

#### UX-002 - Ticket submission idempotency cannot be implemented reliably from the documented workspace

The API requires an `Idempotency-Key` for `POST /resident/tickets` and promises the original result on retry ([api-contracts.md](../api-contracts.md), Resident Surfaces and Idempotency). The browser workspace is specified to contain only subject, content, urgency, schema version, and local timestamp ([data-architecture.md](../data-architecture.md); [frontend-architecture.md](../frontend-architecture.md)). No stable key, pending request state, or ambiguous-response recovery is owned by either side. A timeout after the server commits therefore permits the frontend to generate a new key and create a duplicate ticket, while one implementation may retry and another may restart.

**Required architectural clarification:** generate one key per workspace, retain it until a definitive success/failure result, retry the same key after transport failure, and define the response/query behavior for an unknown outcome. Include the key's account binding and clearing rules in the persistent/transient data and API contracts.

#### UX-003 - `Notify` has two incompatible backend contracts

The frontend says `Notify` opens a resident-preselected composer ([frontend-architecture.md](../frontend-architecture.md), Ticket Detail), while the API lists `POST /manager/tickets/{ticket_id}/notify` as directly creating the notification and separately exposes generic audience preview/send endpoints ([api-contracts.md](../api-contracts.md), Manager Surfaces). There is no request schema for the ticket-specific composer, no preview token/recipient snapshot, and no defined behavior if scope changes while the composer is open. Two teams can both follow the docs and produce either an immediate send button or a draft composer with different confirmation/audit behavior.

**Required architectural clarification:** choose one flow: ticket detail -> composer (subject/content) -> server preview bound to ticket/resident -> explicit send, with a single canonical endpoint or an explicit prepare/send pair. Define audience-change and scope-revocation errors, exact preselection, duplicate-send idempotency, and the accessible success/failure states.

#### UX-004 - Session expiry and re-authentication can leak or discard the wrong ticket workspace

The workspace is account-scoped in `sessionStorage` and is cleared on logout/account switch, but the required UX state “session expired” has no behavior ([frontend-architecture.md](../frontend-architecture.md), Ticket Workspace and Required UX States). A 401 can occur while a resident is composing, and a later login may be the same or a different account in the same tab. The architecture does not define whether the unsent fields are preserved, cleared, or re-associated, nor how the UI prevents a stale workspace from being submitted by another account.

**Required architectural clarification:** bind the workspace to a server-confirmed account/session epoch; on expiry freeze editing and require re-authentication, then restore only for the same account or clear it deterministically. Specify announcements, redirect behavior, and tests for same-account re-login, different-account login, and expired-session submission.

#### UX-005 - Administrator-created account flow has no credential/activation contract

The architecture provides administrator APIs to create resident and manager accounts but specifies no request/response fields or user journey for initial password setup, OTP verification, delivery of temporary credentials, or first-login activation ([authentication-authorization.md](../authentication-authorization.md), Administrator Provisioning; [api-contracts.md](../api-contracts.md), Administrator Surfaces). This is a trust-boundary and usability seam: an implementation can silently set a password, send an untracked credential, or bypass the registry/contact verification that public registration requires.

**Required architectural clarification:** define whether admin creation creates a pending account with an activation/recovery challenge or an immediately active account, how the user proves control of the registry contact, what the admin sees after creation, and how secrets are never displayed or logged.

### IMPORTANT

#### UX-006 - Scope revocation while a manager is viewing a ticket lacks a safe UI/cache rule

The docs require access to be rechecked on every mutation and list a “permission lost” state, but do not say what happens to already-rendered detail data or cached resident/Zalo data after a `404` ([authentication-authorization.md](../authentication-authorization.md), Manager Scope Enforcement; [frontend-architecture.md](../frontend-architecture.md), Required UX States). A compliant client could leave sensitive ticket details on screen and merely disable buttons; another could redirect immediately.

**Required clarification:** on scope failure, purge protected detail and related cached contact data, announce loss of access, and navigate to an in-scope queue/safe landing route. Define behavior for an in-flight `Notify` or terminal action.

#### UX-007 - Registration contact mismatch and recovery states are underspecified

Registration collects both phone and email but accepts “at least one” registry match ([authentication-authorization.md](../authentication-authorization.md), Resident Registration). The docs do not define which contact receives OTP when both match, how a mismatching contact is stored, or how the form explains partial mismatch without revealing registry data. The API's generic eligibility errors and claimed-ID recovery response need concrete field-level UI states and retry limits.

**Required clarification:** return a masked, server-selected verification destination; preserve or reject the non-matching contact by explicit rule; specify resend, wrong-code, expired-code, and already-claimed flows in the UX/API contract.

#### UX-008 - Desktop layout and accessibility requirements need testable interaction details

The baseline is approved (WCAG 2.2 AA, resident and manager desktop-first, 1024 CSS px minimum product viewport), but the architecture leaves several implementation seams: confirmation dialogs show English examples despite Vietnamese-first UX; automatic `Resolving` on detail open needs a non-disruptive status announcement; desktop manager tables/details must expose all required queue fields and actions; and the 400% zoom/320px reflow statement is not mapped to concrete component tests ([frontend-architecture.md](../frontend-architecture.md), Desktop Layout Contract and Accessibility Contract).

**Required clarification:** add a UX accessibility matrix covering localized dialog/error copy, focus return after `Resolved`/`Denied` and Zalo fallback dialogs, live-region announcements for open/conflict/status changes, keyboard/pointer operation of desktop queue tables/details, and desktop viewport/zoom test cases. Administrator UI remains explicitly excluded from the MVP web shell.

#### UX-009 - Read/unread notification state has no complete interaction contract

Only a mark-read endpoint is specified ([api-contracts.md](../api-contracts.md), Resident and Manager Surfaces), while the product calls for a `Read`/`Unread` state. The architecture does not decide whether users can mark notifications unread, whether opening a detail auto-marks read, or how optimistic read updates reconcile after failure.

**Required clarification:** define read-on-open versus explicit read, optional mark-unread, list ordering/badges, and the stale/error announcement behavior. This can remain type/retention-agnostic as requested.

## Positive UX Constraints to Preserve

- Backend-derived resident/location fields remain read-only in the ticket review; the assistant never asks residents to repeat profile data.
- Queue/list reads stay side-effect-free; only the committed full-detail route invokes the open command.
- Terminal actions are explicit, localized confirmation dialogs; `Denied` additionally requires an explanation.
- `Zalo` and `Notify` are detail-only actions, and Zalo fallback never claims external delivery.
- The same manual/chat workspace is used across route changes without a persistent server draft.
- Scope enforcement, conflict notifications, and WCAG 2.2 AA must be represented in loading, empty, permission-lost, stale, and dependency-failure states—not only in API behavior.

## Required UX Artifacts Before Frontend Stories

1. Ticket state/open-race sequence and conflict-state wireflow.
2. Session expiry, same-account re-login, different-account login, and workspace-clearing flow.
3. `Notify` prepare/preview/send flow with audience-change and scope-revocation states.
4. Administrator account provisioning and first-login activation flow.
5. Desktop manager queue/detail behavior at 1024/1280/1440px and required 400% zoom/reflow.
6. Vietnamese accessibility copy and live-announcement matrix for dialogs, status changes, validation, and errors.

