# OnBxrd MVP Frontend State Matrix

This document makes required visible states testable. Stable machine codes and authoritative transition semantics come from [`../architecture/api-contracts.md`](../architecture/api-contracts.md).

## Shared State Rules

| State | Visible behavior | Accessibility behavior | Recovery |
|---|---|---|---|
| Initial loading | Layout-shaped skeleton or concise progress state | Page title remains available; loading state has an accessible label | Resolve to content, empty, or error |
| Background refresh | Keep safe existing content; show non-blocking refresh indicator | Polite announcement only when the result materially changes | Continue using safe content unless scope is revoked |
| Empty data | Explain what is empty and why when known | Heading and text, not icon-only | Relevant approved next action |
| No filter matches | Preserve filters and distinguish from no underlying data | Announce zero matching results | Clear or edit filters |
| Dependency unavailable | Keep unaffected tasks usable | Error summary/region receives focus only after an explicit failed action | Retry; provide manual alternative where approved |
| Validation error | Preserve values and identify fields | Focus error summary on submit; link errors to controls | Correct fields and resubmit |
| Authentication expired | Stop protected mutations and route to Login | Focus Login heading; announce session expiry | Reauthenticate; restore only same-account-safe state |
| Permission/scope lost | Purge protected data before safe navigation | Assertive announcement without protected object details | Reload `/auth/me`; continue in current scope |
| Success | Keep result visible in page/history | Polite announcement; focus only when necessary for the next task | Continue or navigate to created resource |
| Stale/conflict | Preserve user intent where safe; show current server state | Announce conflict and move focus to review controls | Explicit reconciliation or refresh |

Toasts may supplement these states but cannot be their only representation.

## Theme State Matrix

| State | Required UX | Persistence / recovery | Accessibility and motion |
|---|---|---|---|
| First visit, no hint | Resolve `prefers-color-scheme`; fall back to Light | No account assumption | Apply before first paint where feasible; no announcement needed |
| Signed-out explicit switch | Apply Light or Dark immediately | Store only a non-sensitive device hint | Control names current and target theme; preserve focus/scroll |
| Authenticated profile loaded | Backend profile preference wins | Mirror resolved preference as pre-paint hint | If reconciliation changes theme, use one `motion.standard` token transition or instant under reduced motion |
| Authenticated switch saving | Apply selected theme without blocking the current task; show quiet saving state only if latency is visible | Persist through the approved profile theme field | Do not disable unrelated controls or replay route motion |
| Preference save failed | Keep the locally selected appearance for the current device/session and state that cross-device preference was not saved | Retry through the normal profile mutation; do not claim durable persistence | Durable inline/Toast feedback; no theme rollback flash unless product logic requires it |
| Unsupported/corrupt hint | Ignore it and resolve device preference, then Light | Replace with a valid hint after explicit selection | No error surface unless profile contract itself fails |
| Reduced motion | Same visual theme result | Same persistence | Token swap is immediate or opacity-only <=80ms; no radial wipe, spring, stagger, or layout motion |

Every component state in this matrix must be visually complete in Light and Dark. Theme switching must not reset page, form, draft, dialog, selection, loading, or conflict state.

## Authentication State Matrix

| Flow | State | Required UX |
|---|---|---|
| Login | Idle | Username/password fields, Login action, Register and Recovery links |
| Login | Submitting | Prevent duplicate activation; retain field values; announce progress once |
| Login | Invalid credentials | Generic localized error; do not disclose which field matched |
| Login | Rate limited | Show retry timing when returned and retain safe values |
| Login | Deactivated/revoked | Explain that access is unavailable without exposing administrative details |
| Login | Success | Fetch `/auth/me`, establish the correct shell, rotate focus to destination heading |
| Registration | Role selection | Resident and Manager only; no Administrator option |
| Registration | Field entry | Role-appropriate registry ID label plus shared username/password/phone/email fields |
| Registration | Eligibility mismatch | Generic identity-safe response; no registry contact disclosure |
| Registration | Identity claimed | Login and Recovery actions |
| Registration | OTP sent | Show server-selected channel, masked destination, expiry, and resend timing |
| Registration | OTP invalid | Field-linked error; attempts remaining only if safely returned |
| Registration | OTP expired | Explain expiry and offer allowed resend/restart behavior |
| Registration | Attempts exhausted | Challenge invalidated; return to safe restart state |
| Registration | Provider unavailable | Preserve non-secret input where safe; retry without claiming delivery |
| Registration | Activated | Session established only after backend success; route by `/auth/me` role |
| Recovery | Challenge started | Show masked destination without identity disclosure |
| Recovery | OTP/password stages | Same invalid, expired, exhausted, and rate-limited behavior as registration |
| Recovery | Complete | Explain credential reset and session behavior; provide safe next route |

## Resident Page State Matrix

| Page | Loading | Empty | Error/unavailable | Success/current state | Special states |
|---|---|---|---|---|---|
| Onboarding | Step-list skeleton | No configured steps, distinct from completed | Definition/progress unavailable | Ordered progress and next action | Completed, current, pending, blocked, completion mutation pending/failure |
| Benefits | Benefit-card skeleton | No applicable benefits | Benefits unavailable | Applicable benefit list | Detail expansion/drawer |
| Assistant | Conversation loading only when restoring current in-memory context | Fresh conversation prompt | Assistant/knowledge unavailable with manual-ticket fallback | Grounded answer and citations | Unsupported answer; ticket intent; stale proposal; replacement review |
| Ticket history | Ticket-card/row skeleton | No submitted tickets | History unavailable | Cursor list | No filter matches; status refresh |
| Ticket workspace | Draft/context skeleton | No active draft before explicit start result | Save unavailable; validation errors | Editable/resumed draft | Existing draft, saving, saved, conflict, generation gone, session expired, submitting, outcome unknown |
| Ticket detail | Detail/timeline skeleton | Not applicable; unknown ID is not-found | Own-ticket unavailable/not found | Snapshot, status, history | Denied explanation; terminal result |
| Notifications | Notification-list skeleton | No notifications | List/read mutation unavailable | Read/unread list | Related-resource missing; explicit read action |
| Profile | Profile skeleton | Not applicable | Profile/contact provider unavailable | Verified data and allowed edits | Contact OTP, password change, Zalo validation, immutable correction guidance |

## Persistent Draft State Machine

```text
NO_DRAFT
  -> STARTING
  -> EDITING

EXISTING_DRAFT
  -> RESUME_CHOICE
     -> EDITING
     -> REPLACE_CONFIRMATION
        -> REPLACING
        -> EDITING(new draft_id, version 1)

EDITING
  -> SAVING
     -> EDITING(saved)
     -> SAVE_UNAVAILABLE
     -> CONFLICT_REVIEW
     -> GENERATION_GONE

EDITING
  -> REVIEW
  -> SUBMITTING
     -> SUBMITTED
     -> VALIDATION_ERROR
     -> OUTCOME_UNKNOWN
        -> RETRYING_SAME_KEY
        -> SUBMITTED
```

### Draft state requirements

| State | Editable? | Navigation | Required message/action |
|---|---:|---|---|
| No draft | No until explicit start succeeds | Safe to leave | Start draft through explicit intent or direct editor behavior |
| Starting | No | Prevent duplicate start action | Loading state; start uses idempotency key |
| Editing, unsaved | Yes | Internal leave waits or confirms | Explain unsent values are not yet durable |
| Saving | Yes; later input remains buffered | Internal leave waits or confirms | Coalesced Saving indication |
| Saved | Yes | Safe for acknowledged values | Saved means exact displayed values are server-acknowledged |
| Save unavailable | Yes in memory | Warn before leaving; hard close cannot guarantee preservation | Retry; explain other devices see last saved version |
| Conflict review | Edit fields through comparison controls | Prevent ordinary autosave until resolved | Announce another session update; server values selected by default |
| Generation gone | No old-generation mutation | May navigate to proven ticket/history/new flow | Do not claim discard/replace/submit cause without proof |
| Review | Allowed to return to editing | Remain on same route | Separate editable fields from verified context |
| Submitting | No fingerprint-changing edits | Prevent route change that would obscure result | Accessible pending result; same request/key |
| Outcome unknown | No fingerprint-changing edits | Reload recovery allowed for same account | Retry same POST/key; never start a new draft |
| Submitted | No draft remains | Link to created ticket | Durable success and cleared caches |

## Draft Conflict Comparison

For each of Subject, Content, and Urgency, display:

- Latest server value
- Resident's attempted local value when different
- Selection control defaulted to server value
- Clear Apply selected local values action

Unchanged fields should not create unnecessary choices. The submitted reconciliation patch contains only explicitly selected local fields and uses the returned current `draft_id` and version.

## Assistant Proposal States

| Condition | Behavior |
|---|---|
| No ticket intent | Show grounded answer/citations only |
| Ticket intent, no active draft | Start/return draft, then show proposed Subject/Content/Urgency |
| Ticket intent, existing draft | Show Resume or Discard and start new before proposal mutation |
| Proposal matches current draft generation/version/fingerprint and targets unchanged empty fields | May offer one explicit Apply action; do not submit |
| Proposed field is non-empty or changed since observation | Show field-specific replacement choice |
| Fingerprint or generation mismatch | Treat all affected values as explicit review proposals |
| Assistant unavailable | Keep conversation error visible and provide manual ticket link |
| Unsupported question | Show approved unavailable-answer response, not a fabricated answer |

## Submission Recovery States

| Event | Required behavior |
|---|---|
| Before request | Store only approved account-bound attempt metadata in `sessionStorage` |
| Duplicate click | UI suppresses extra activation; backend idempotency remains authoritative |
| Validation failure | Show errors, clear attempt metadata, allow edit, derive a new key only after changed definitive retry input |
| Transport failure after send | Enter Outcome unknown and reuse the same POST/key |
| Hard reload with metadata | Call `/auth/me`; restore only for same account and retry same POST/key |
| Different account after reload | Purge attempt metadata before protected content renders |
| Committed original request | Retry returns original ticket and transitions to Submitted |
| Browser-session metadata lost | Direct to Ticket history; do not infer result |

## Manager Page State Matrix

| Page | Loading | Empty | Error/unavailable | Success/current state | Special states |
|---|---|---|---|---|---|
| Work home | Shell/cards skeleton | No scope grants or no recent items | Individual section unavailable without collapsing all navigation | Work-area links and supported recent items | Partial cursor data must be labeled honestly |
| Residents | Resident-list skeleton | No scoped residents | Registry/scope dependency unavailable | Scoped cursor list | No filter matches; `scope_changed` |
| Onboarding | Progress-list skeleton | No scoped residents/progress | Progress or registry unavailable | Scoped progress rows | Incomplete/blocked; no manual reminder action |
| Ticket queue | Ticket-list skeleton | No scoped tickets | Queue/scope unavailable | Side-effect-free cursor list | No filter matches; scope changed |
| Ticket detail | Detail skeleton while open command runs | Not applicable | Protected not-found/scope lost | Current authorized detail | Open transitioned, already current, open conflict, terminal conflict, Zalo fallback, Notify preview stale |
| Notifications | Inbox/composer skeletons independently | No notifications; no preview audience | List/preview/send unavailable | Read/unread list or composer | Empty audience, preview stale, campaign accepted |
| Profile | Profile/scope skeleton | No grants is a valid state | Profile or registry dependency unavailable | Identity/preferences/read-only scope | Contact/password change; scope refresh |

## Manager Ticket Open State Machine

```text
QUEUE_OBSERVATION
  -> DETAIL_ROUTE_COMMITTED
  -> OPENING(observed_status, expected_version, attempt_key)
     -> TRANSITIONED_TO_RESOLVING
     -> ALREADY_CURRENT
     -> OPEN_CONFLICT
     -> SCOPE_LOST
     -> DEPENDENCY_UNAVAILABLE
```

| Result | Detail visibility | Announcement | Available next actions |
|---|---|---|---|
| Transitioned | Keep detail | Pending changed to Resolving | Zalo, Notify, permitted terminal actions |
| Already current | Keep detail | Current state only; no false conflict | Actions allowed by current state |
| Open conflict | Keep safe returned detail | Another manager opened it first; current state named | Current-state actions and conflict notification |
| Scope lost/not found | Purge detail before navigation | Access changed; no existence disclosure | Return to safe Manager page |
| Dependency unavailable | Do not claim transition | Service unavailable | Retry open with safe idempotency behavior |

## Terminal Transition States

| Action | Preconditions in UI | Confirmation | Success | Conflict |
|---|---|---|---|---|
| Resolved | Returned capability and current non-terminal state | Localized dialog, Cancel focused | Current state/history updated and announced | Replace with server state; explain another manager acted |
| Denied | Returned capability plus non-empty explanation | Localized dialog including denial intent, Cancel focused | State/history and denial explanation updated | Preserve explanation locally only while safe; replace current server state |

Confirmation never substitutes for backend validation.

## Zalo States

| Result | UX |
|---|---|
| Normalized URL returned | Open new external context with `noopener`, `noreferrer`, and no-referrer policy |
| Notify fallback returned | Show fallback dialog; offer ticket Notify |
| Navigation blocked before handoff | Show the same fallback dialog |
| External context accepted | Record only that OnBxrd attempted handoff; make no profile/delivery/read claim |
| Scope lost | Purge detail/contact data and navigate safely |

## Notification Composer State Machine

```text
EDITING
  -> PREVIEWING
     -> PREVIEW_READY
     -> EMPTY_AUDIENCE
     -> PREVIEW_ERROR

PREVIEW_READY
  -> SENDING
     -> CAMPAIGN_ACCEPTED
     -> PREVIEW_STALE
     -> OUTCOME_UNKNOWN_RETRY_SAME_KEY
     -> SEND_ERROR
```

| State | Required UX |
|---|---|
| Editing | Subject, Content, and allowed audience controls; ticket Notify audience is read-only |
| Previewing | Disable send; preserve form values |
| Preview ready | Audience summary, recipient count, expiry context, explicit Send |
| Empty audience | Prevent send and return focus to audience controls/summary |
| Preview stale | State that nothing was sent; require refreshed preview and review |
| Sending | Prevent duplicate activation; keep reviewed content visible |
| Campaign accepted | State that the campaign was accepted, not delivered/read |
| Outcome unknown | Retry same preview token/request/key according to API idempotency |
| Scope lost | Purge preview and protected audience data before safe navigation |

## Notification Read States

- `read_at = null` is Unread.
- Listing and background refresh preserve the state.
- Opening an item invokes Mark read once idempotently.
- An explicit Mark as read action is provided for items without a detail-opening interaction.
- A failed read mutation restores or preserves the server-known unread state and announces the failure without refreshing the entire list context.
- Mark unread is not part of the MVP contract.

## Scope and Cache Purge Matrix

| Trigger | Purge requirements |
|---|---|
| Logout | All protected query data, unsaved buffers, previews, and submit metadata for the session |
| Account switch | Previous account's complete protected cache before new protected rendering |
| `scope_changed` | Manager resident, onboarding, ticket, notification audience, contact, and preview caches; then reload `/auth/me` |
| Protected Manager `404` | Current resource plus related resident/contact/preview data |
| Session expiry | Stop mutations; keep only account/epoch-bound unsaved memory until reauthentication decision |
| Different account after expiry | Purge frozen buffer and metadata before rendering |

## State Testing Checklist

- Each route demonstrates loading, empty, error, success, and session behavior.
- Every conflict preserves safe user intent and displays current server state.
- No stale generation or stale ticket state is silently overwritten.
- Ambiguous submissions and sends reuse their original idempotency context.
- Scope loss removes protected data before navigation or back restoration.
- Important results remain visible without depending on toasts.
