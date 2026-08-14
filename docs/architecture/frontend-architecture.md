# Frontend Architecture

## Application Shape

Use one TypeScript Next.js 16.3.x/React 19.2.x web application on Node.js 22 LTS with role-specific route shells. Exact patch versions are committed in the frontend lockfile at implementation kickoff.

```text
app/
  (public)/login, register, recovery
  resident/onboarding, benefits, assistant, tickets, notifications, profile
  manager/dashboard, residents, onboarding, tickets, notifications, profile
  admin/accounts, corrections
```

Route rendering may hide unavailable navigation, but route guards are convenience only. The backend independently authorizes every resource.

## State Ownership

| State | Owner | Persistence |
|---|---|---|
| Authenticated principal and display scope | Backend `/auth/me`; cached by web client | Server session |
| Resident/manager lists and ticket detail | Backend | Client query cache only |
| Active ticket draft fields/generation/version | Backend draft API; cached by draft query/provider | PostgreSQL; client query cache and unsaved memory buffer only |
| Pending submit recovery metadata | Frontend, account-bound | `sessionStorage` only: account ID, `draft_id`, version, fingerprint, idempotency key; never draft fields |
| Resident snapshot shown during ticket review | Backend profile/draft review endpoints | Read-only client cache; never draft-field authority |
| Dialog/open/selection state | Component/page | Memory only |
| Notification campaign preview/send and read state | Backend | PostgreSQL; preview token cached in memory only |

The web client uses one API client layer for credentials, CSRF, correlation IDs, stable errors, and response decoding. Feature components do not call provider endpoints directly.

## Persistent Ticket Draft

The server draft is the only authoritative ticket-creation state. Do not persist draft fields in `localStorage`, `sessionStorage`, service-worker caches, or URL state. The sole browser-persistent exception is non-sensitive pending-submit recovery metadata in `sessionStorage`: confirmed account ID, `draft_id`, version, field fingerprint, idempotency key, and start time. It contains no subject, content, urgency, profile, or location values.

Requirements:

- manual form and assistant apply generation-and-version-bound patches to the same server draft;
- assistant patches include the observed `draft_id`, version, and server-computed field fingerprint. They fill unchanged empty fields and present changed/non-empty fields as replacement proposals rather than silently overwriting resident input; a fingerprint mismatch triggers the same explicit per-field review and never auto-applies;
- resident profile/location is fetched read-only from the API and displayed separately;
- route navigation, refresh, logout/login, and another authenticated browser/device reload the same saved draft;
- autosave after 750 ms of inactivity and on field blur, using one single-flight/coalescing save queue per draft generation. Only one mutation is in flight; later keystrokes remain buffered and are rebased onto the accepted response before the next patch;
- visible save states are `saving`, `saved`, `offline/unavailable`, and `conflict`. `Saved` means the server acknowledged the exact values currently displayed; delayed responses older than the cached `(draft_id, version)` are ignored;
- internal navigation awaits the current save or requires explicit leave confirmation. Hard refresh/tab close may warn but must not promise that unsent values will persist. Offline copy states that other devices see only the last server-saved version;
- logout never deletes the saved draft. Session expiry freezes the edit buffer above the public/authenticated route boundary, bound to the last confirmed account ID and `session_epoch`. After login, call `/auth/me`; restore it only when the account ID matches, then rebind it to the newly confirmed epoch. Otherwise purge it before protected data renders;
- account switch immediately purges the prior account's query cache and unsaved buffer before requesting the new account's draft;
- derive one reproducible submission idempotency key from the submitted draft generation/version/fingerprint, store the non-sensitive attempt metadata in account-bound `sessionStorage` before sending, reuse it through ambiguous outcomes and hard reload, and generate a new key only after a definitive validation failure followed by an edit; and
- successful submission or explicit discard removes the draft from all client caches.

### Start, resume, and replace

Entry behavior distinguishes continuation from a new-ticket intent:

1. Direct navigation/deep-link to the editor, refresh, same-account login recovery, or cross-device continuation loads the active draft and resumes it without a replace prompt.
2. An explicit `New ticket` action calls start. If the server reports `existing`, show its last-updated summary and choices `Resume draft` and `Discard and start new`.
3. An assistant-detected new-ticket intent follows the same choice before any proposal mutates an existing draft.
4. Focus `Resume draft` as the safe default. Replacement requires an accessible confirmation dialog.
5. Replacement calls the single atomic replace endpoint, returns a new `draft_id` generation, and never performs discard-then-start or creates a second draft.

### Concurrent editing

Every mutation uses the currently rendered `draft_id` and version plus a fresh idempotency key. On `ticket_draft_conflict`:

- preserve the resident's attempted changes in memory;
- replace the displayed server baseline/version with the returned current draft;
- announce that the draft changed in another session;
- show a clear per-field comparison for subject, content, and urgency, defaulting each field to the latest server value;
- let the resident explicitly select individual local field values to apply, then send only those selected fields against the returned current version; and
- preserve unsent local text and repeat review after another conflict; never auto-merge, force-overwrite, or silently retry.

On `ticket_draft_generation_gone`, stop the save queue and explain that this draft is no longer active; link to the same-account ticket only when the response supplies a proven submitted result. Never guess whether another session discarded or replaced it, and never apply local changes to a later generation automatically.

While submission is `submitting` or `outcome_unknown`, prevent edits that change the submitted fingerprint and keep the resident in an accessible non-editable pending-result state. On reload, call `/auth/me`, restore the attempt only for the same account, and retry the same POST/key; a committed result returns the original ticket before draft lookup. A different account purges the attempt before protected rendering. After definitive success or validation failure, clear the recovery metadata; after browser-session loss, fall back to ticket history. A stale save received after submission must not start another draft automatically.

## Ticket Detail and State Mutation

Manager queue rows and previews are read-only. The full detail route calls `POST /manager/tickets/{id}/open` only after navigation commits and the manager is authenticated, using the queue/detail observation plus one attempt key.

- `PENDING` becomes `RESOLVING` automatically on the first authorized full-detail open.
- A concurrent opener that observed the same stale `PENDING` version receives `ticket_open_conflict`; keep authorized detail visible, announce that another manager opened it first, update the state/version, and surface the persisted conflict notification.
- Later opens that observed current `RESOLVING` are ordinary detail views and show no conflict.
- A `Resolved` action opens an accessible localized confirmation dialog, for example: `Bạn có chắc muốn đánh dấu yêu cầu này là "Đã giải quyết" không?`
- A `Denied` action requires an explanation and then opens an accessible localized confirmation dialog, for example: `Bạn có chắc muốn từ chối yêu cầu này không?`
- Confirmation is not a backend authorization signal; the transition API still validates scope/state/version.
- On `409 ticket_state_conflict`, keep the manager on the detail page, replace stale state with the returned current state, explain that another manager changed the ticket, and surface the persisted conflict notification.

`Zalo` and `Notify` appear only on full ticket detail. `Notify` opens a subject/content composer whose audience is server-preselected to that ticket resident. The user reviews a server preview and explicitly sends; the button never sends immediately. A stale preview remains unsent and requires refresh. Missing/invalid Zalo shows a dialog that recommends `Notify` without claiming a notification was sent. A returned Zalo URL is opened in a new external context with `noopener`, `noreferrer`, and no-referrer policy; the client never broadens or reconstructs the destination.

If manager scope changes or is revoked while a protected detail/composer is open, purge that detail, preview token, resident/contact data, and related query-cache entries before redirecting to a safe manager route. Do not leave protected content behind a disabled overlay or browser back-cache.

## Desktop Layout Contract

### Supported widths

- Resident and manager workflows are desktop-first.
- Minimum product-supported viewport: `1024 CSS px` at 100% browser zoom.
- Standard desktop: `1024-1279 px`.
- Wide desktop: `1280-1439 px`.
- Extra-wide desktop: `1440 px` and above.
- Mobile and tablet-specific layouts, navigation, and acceptance testing below `1024 CSS px` at 100% zoom are outside MVP scope.
- WCAG reflow at `320 CSS px` equivalent content width under 400% desktop zoom remains required accessibility behavior and does not imply mobile support.

### Resident shell

- Desktop-first at 1024 px and above.
- Primary navigation remains reachable without hover.
- Forms use a clear primary task column and may add a contextual side rail when space permits.
- Ticket review keeps read-only resident context visually separate from editable fields.

### Manager shell

- Desktop-first multi-column/dashboard layout at 1024 px and above.
- Queue, detail, filtering, and action layouts are optimized for desktop pointer and keyboard use.
- Dense data remains in desktop tables or deliberate master-detail layouts; mobile card conversions are not required.
- Required data and actions remain available throughout the supported desktop range and WCAG zoom/reflow states.

## Accessibility Contract

WCAG 2.2 AA is binding.

- Full keyboard access, visible focus, logical focus order, and skip navigation.
- Semantic landmarks/headings and explicit form labels.
- Status is expressed by text and programmatic state, never color alone.
- Dialog focus is trapped, labeled, announced, and returned to its trigger.
- Ticket transitions, OTP errors, validation, notification state, and conflict results use appropriate live-region announcements.
- Draft save announcements are coalesced so screen readers are not told `saving`/`saved` on every keystroke.
- Pointer targets meet WCAG 2.2 target-size expectations or documented exceptions.
- Reflow at 400% zoom and 320 CSS px equivalent content width must not lose core functionality. This is a desktop accessibility requirement, not a supported mobile viewport.
- Theme changes preserve contrast, focus, and reduced-motion preferences.
- Vietnamese strings are the default and must not be embedded in business logic.

### Interaction matrix

| Flow/state | Focus and keyboard | Programmatic announcement |
|---|---|---|
| Registration OTP sent | Move focus to code heading/input; resend remains keyboard reachable | Announce server-selected masked destination and expiry without reading the full contact |
| Field validation | Move to error summary only on submit; link errors to fields | Announce error count and field-specific errors |
| Explicit New ticket with existing draft | Focus the resume/replace dialog; default to Resume | Announce last-updated context and that replacement discards saved work |
| Direct resume of active draft | Focus the draft heading/editor; no replacement dialog | Announce that the saved draft was resumed |
| Session expired with ticket work | Move to login heading; retain the account/epoch-bound memory buffer above the route boundary | Announce that server-saved work remains; unsaved work returns only after the same account is confirmed |
| Draft version conflict | Focus field-by-field conflict review and preserve attempted changes | Assertive announcement that another session updated the draft; no silent overwrite |
| Ticket open conflict | Keep focus in detail heading/status region | Polite live announcement naming current status and another-manager conflict |
| Terminal confirmation | Trap focus, default to safe cancel, return to trigger | Dialog name includes chosen terminal action; denial reason error is associated |
| `Notify` preview/send | Focus preview heading, then success/error summary | Announce recipient count, stale preview, accepted campaign, or failure |
| Scope revoked | Move focus to safe page heading after cache purge | Assertive announcement that access changed; do not disclose removed resource details |
| Zalo unavailable | Trap focus in fallback dialog and return to `Zalo` trigger | State link unavailable and offer `Notify`; no delivery claim |
| Notification opened/read | Preserve list position on return | Announce read-state change without refreshing the entire list context |

## Required UX States

Every role surface defines loading, empty, validation error, dependency unavailable, permission lost, session expired, retry, success, and stale-data/conflict states.

Architecture-sensitive cases include:

- registry/OTP unavailable during registration;
- registration response with server-selected masked OTP destination;
- ID already claimed with login/recovery actions;
- manager has no scope grants;
- manager scope revoked while detail is open;
- Zalo URL missing or invalid;
- assistant unavailable while manual ticket entry remains usable;
- existing draft when starting a new ticket flow;
- draft save unavailable or version conflict across sessions/devices;
- notification audience changes after preview; and
- terminal ticket conflict after another manager acts.

Notification lists do not mark rows read during fetch, viewport exposure, or background refresh. Opening a notification calls the idempotent read endpoint; an explicit `Mark as read` control is available where no detail view exists.

## Frontend/Backend Contract Ownership

- Frontend owns presentation, unsaved edit buffers, resume/replace confirmation, accessibility, and visible conflict recovery.
- Backend owns the persistent account draft, identity, scope, resident snapshots, ticket state, concurrency, audience resolution, and durable notifications.
- Shared API schemas are generated or validated from backend OpenAPI; frontend types must not diverge manually.
