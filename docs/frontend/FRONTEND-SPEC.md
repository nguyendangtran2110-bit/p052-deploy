# OnBxrd MVP Frontend Specification

- **Status:** Approved-scope implementation specification
- **Frontend scope:** Public/authentication, Resident, and Manager only
- **Primary language:** Vietnamese
- **Required accessibility level:** WCAG 2.2 AA
- **Application architecture:** TypeScript Next.js 16.3.x / React 19.2.x web client

## 1. Authority and Purpose

This document translates the approved MVP product and architecture into an implementation-ready frontend contract. It does not redefine backend behavior, product scope, authorization, persistent data, or API schemas.

Authority remains, in order:

1. [`../PRD.md`](../PRD.md)
2. [`../architecture/ARCHITECTURE-SPINE.md`](../architecture/ARCHITECTURE-SPINE.md)
3. Approved architecture and ADRs under [`../architecture/`](../architecture/)
4. This frontend specification and its supporting documents

For request and response schemas, error codes, idempotency, and authorization behavior, use [`../architecture/api-contracts.md`](../architecture/api-contracts.md). Frontend types must be generated from or validated against the backend OpenAPI contract rather than maintained as an independent schema source.

Supporting implementation references:

- [`ROUTE-MAP.md`](ROUTE-MAP.md): route ownership, access, navigation, and page/API mapping
- [`STATE-MATRIX.md`](STATE-MATRIX.md): required page and concurrency states
- [`COMPONENT-MAP.md`](COMPONENT-MAP.md): reusable component and state-owner boundaries
- [`ACCESSIBILITY.md`](ACCESSIBILITY.md): WCAG, keyboard, focus, announcements, and responsive accessibility
- [`mock-data/README.md`](mock-data/README.md): mock API and scenario strategy

## 2. Approved MVP Scope

The MVP frontend contains 18 user-facing pages:

- 3 public/authentication pages
- 8 resident pages
- 7 manager pages
- 0 administrator pages

Administrator product requirements and backend contracts remain authoritative future scope, but the MVP frontend must not expose administrator routes, navigation, dashboards, or responsive requirements.

### Explicit frontend non-goals

- Administrator UI of any kind
- Manager analytics, KPI dashboards, reports, surveys, or unsupported aggregate metrics
- Benefit or chatbot-source governance UI
- Onboarding-definition management UI
- Notification catalog, retention, or sent-campaign history UI
- Ticket attachments, categories, reopening, cancellation, escalation, SLA controls, or manager approval
- Live Zalo messaging, Zalo API access, profile-existence checks, profile-ownership verification, or delivery/read claims
- Anonymous or browser-local persistent ticket drafts
- Client-side role, scope, ticket-state, or audience authority

## 3. Approved Page and Route Inventory

| Page | Route | Actor | Primary responsibility |
|---|---|---|---|
| Login | `/login` | Public | Authenticate and enter the correct role shell |
| Registration and activation | `/register` | Public | Select Resident or Manager, register, verify OTP, and activate an account |
| Account recovery | `/recovery` | Public | Complete verified credential recovery |
| Onboarding | `/resident/onboarding` | Resident | Show ordered onboarding progress and allowed next actions |
| Benefits | `/resident/benefits` | Resident | Show benefits applicable to the authenticated resident |
| Building assistant | `/resident/assistant` | Resident | Answer grounded questions and propose bounded ticket-field updates |
| Ticket history | `/resident/tickets` | Resident | List current and historical tickets |
| Ticket workspace | `/resident/tickets/new` | Resident | Resume/start the one active draft, edit, review, and submit |
| Ticket detail | `/resident/tickets/{ticketId}` | Resident | Show the submitted snapshot, state, events, and denial explanation |
| Notifications | `/resident/notifications` | Resident | Show resident notification history and read state |
| Profile and preferences | `/resident/profile` | Resident | Show verified profile data and edit allowed owner-controlled fields |
| Manager work home | `/manager/dashboard` | Manager | Provide contract-supported navigation and simple work entry points |
| Resident directory | `/manager/residents` | Manager | List residents within current exact scope |
| Onboarding oversight | `/manager/onboarding` | Manager | Show in-scope resident onboarding progress |
| Ticket queue | `/manager/tickets` | Manager | List and filter scoped tickets without state mutation |
| Ticket detail and actions | `/manager/tickets/{ticketId}` | Manager | Open detail, contact the resident, and perform allowed transitions |
| Notifications and composer | `/manager/notifications` | Manager | Read manager notifications and send scoped resident campaigns |
| Manager profile | `/manager/profile` | Manager | Show identity, preferences, contacts, and read-only assignments |

No separate pages are created for registration OTP, recovery OTP, ticket review, benefit detail, notification detail, onboarding resident detail, ticket Notify, Zalo fallback, contact verification, password change, draft replacement, conflict reconciliation, or terminal confirmation. These are page states, drawers, dialogs, or stepper stages.

## 4. Application and Navigation Shape

### Public shell

- Contains the OnBxrd identity, language-correct page title, and only the links relevant to login, registration, and recovery.
- Does not show resident, manager, or administrator navigation before `/auth/me` confirms a principal.
- Does not expose a role-switch control. The active backend-confirmed account role selects the application shell.

### Resident shell

- Mobile-first and usable from 360 CSS px.
- Primary navigation exposes Onboarding, Benefits, Assistant, Tickets, Notifications, and Profile.
- `New ticket` is a prominent intent action that enters `/resident/tickets/new` and follows the active-draft rules.
- On small screens, navigation may use a bottom bar or compact menu, but every destination remains keyboard and screen-reader reachable without hover.
- `/resident` redirects to `/resident/onboarding` unless implementation evidence supports a more useful contract-backed landing without adding a page.

### Manager shell

- Desktop-first at 1024 CSS px and above, responsive to 360 CSS px.
- Primary navigation exposes Work home, Residents, Onboarding, Tickets, Notifications, and Profile.
- `/manager` redirects to `/manager/dashboard`.
- The dashboard is a navigational work home, not an analytics surface. It may show direct links and limited recent items already returned by approved list contracts. It must not imply complete totals when only a cursor page has been loaded.
- At compact widths, dense rows become cards or responsive rows without hiding required fields or actions.

### Navigation behavior

- Preserve the user's previous list filters and scroll position when returning from a detail route during the same browser session where practical.
- Opening a resident notification follows its related-resource reference only after marking it read idempotently. If no detail destination exists, reveal its content inline.
- Queue prefetching and link preview must never call the manager ticket open command.
- Internal navigation away from a ticket draft awaits the current save or presents an explicit leave warning when unsent changes remain.
- Browser back navigation after scope loss must not reveal purged protected content from the query cache or back-forward cache.

## 5. Authentication and Session UX

### Shared registration flow

`/register` is one user-facing flow with these stages:

1. Select Resident or Manager.
2. Enter username, password, phone, email, and the appropriate registry ID.
3. Submit to the corresponding approved resident or manager registration endpoint.
4. Show the server-selected OTP channel, masked destination, and expiry.
5. Verify the challenge.
6. On success, establish the session and route by `/auth/me` role.

The frontend must not let the user choose an unmatched verification destination or reveal whether a registry record exists. `identity_already_claimed` provides Login and Recovery actions without exposing registry details.

### Login and recovery

- Login accepts username and password only.
- Recovery is a single multi-step page covering challenge creation, OTP verification, and password reset.
- Rate limiting, invalid/expired OTP, exhausted attempts, provider unavailability, and generic identity-safe failures remain visible on the page; a toast alone is insufficient.
- Successful password change or recovery reflects session rotation and invalidation rules from the authentication contract.

### Session establishment

- Call `/auth/me` before protected role content renders.
- Render the shell only after the backend-confirmed role, account ID, `session_epoch`, and manager `scope_version` where applicable are known.
- Route guards improve navigation but are not a security boundary. Every API request remains backend-authorized.
- Resident routes opened by a manager and manager routes opened by a resident go to the actor's safe landing page with a user-safe capability message. Do not render protected destination content first.
- Unauthenticated protected-route access redirects to `/login` with an internal return target. Validate the return target as same-origin and route-allowlisted.

### Session expiry and account change

- On `401 authentication_required`, stop protected mutations and move focus to the login page heading.
- A resident draft remains server-persistent. Any unsaved memory buffer is frozen above the route boundary and remains bound to the last confirmed account ID and `session_epoch`.
- After login, restore the buffer only if `/auth/me` confirms the same account. Rebind it to the new epoch after refetching the server draft.
- Before rendering a different account, purge the previous account's query cache, draft buffer, submit recovery metadata, resident/contact data, preview tokens, and manager protected caches.
- Logout clears browser caches and revokes the session but does not discard the server draft.

## 6. Resident Flows

### Onboarding

- Present ordered steps with textual states: completed, current, pending, and blocked when provided.
- Show progress and the next required action without relying on color.
- Resident-controlled completion calls the approved step completion endpoint and updates only after server acceptance.
- Building links, including the official Zalo group join link, are content actions and are distinct from the resident's personal Zalo profile link.
- Do not add document uploads or evidence collection.

### Benefits

- Show only backend-returned applicable benefits.
- Each item presents eligibility, conditions, operating information, and how to use it.
- Benefit details use an inline expansion or responsive drawer rather than a required detail route.
- Do not expose editing, governance, or unsupported benefit-use tracking.

### Building assistant

- Support Vietnamese question entry, grounded answers, citations, and the explicit unavailable-answer response.
- Assistant unavailability must not block navigation to manual ticket creation.
- The assistant may propose only Subject, Content, and Urgency.
- Verified name, phone, building, floor, and room remain read-only backend data and never appear as assistant-owned fields.
- A new-ticket intent must resolve the active-draft Resume or Discard and start new choice before any assistant proposal mutates the draft.
- Assistant proposals tied to a stale generation/version/fingerprint become explicit field replacement proposals; they never silently overwrite resident input.

### Ticket history and detail

- The list displays subject, urgency, status, submission date, and enough context to distinguish tickets.
- Status uses localized text and programmatic state, not color alone.
- Detail displays the immutable submission snapshot, current status, ordered event history, and denial explanation when status is `DENIED`.
- Resident ticket detail is read-only and never changes state.
- Successful submission links directly to the created ticket and leaves the result visible beyond a transient toast.

### Notifications

- Listing, viewport visibility, and background refresh never mark a notification read.
- Opening an item invokes the idempotent read endpoint.
- Provide an explicit Mark as read action where the item has no detail opening action.
- Preserve list position when returning from related content.

### Profile and preferences

- Display immutable username, registry ID, and verified location as read-only.
- Allow only editable fields returned by profile metadata.
- Display name and theme/preferences use the profile endpoint.
- Phone/email replacement uses the verified contact-change challenge and never a direct profile patch.
- Password change uses the approved password endpoint and informs the user that other sessions are revoked.
- Personal Zalo link editing uses the approved local rule-based contract. Frontend validation may provide immediate assistance but cannot broaden backend acceptance.
- Describe accepted Zalo input as a structurally validated link, never as a verified or confirmed profile.

## 7. Persistent Ticket Draft UX

### State ownership

- The backend draft is the only authoritative ticket-creation state.
- Browser memory may hold unsaved keystrokes and UI state.
- Draft fields must not be persisted in `localStorage`, `sessionStorage`, IndexedDB, service-worker caches, URL parameters, analytics, or logs.
- `sessionStorage` may contain only the approved non-sensitive pending-submit recovery metadata: confirmed account ID, `draft_id`, expected version, field fingerprint, idempotency key, and start time.

### Direct resume and explicit new-ticket intent

- Direct navigation, refresh, same-account reauthentication, or device continuation loads `/resident/tickets/new` and resumes an active draft without a replacement prompt.
- An explicit `New ticket` action calls draft start.
- If start returns `existing`, show last-updated context and the choices Resume draft and Discard and start new.
- Resume is the safe default and receives initial focus.
- Replacement requires a second accessible confirmation and calls the single atomic replace endpoint.
- Never implement replacement as discard followed by start.

### Editing and autosave

- Editable fields are Subject, Content, and Urgency only.
- Verified resident and location context is visually separated and read-only.
- Autosave after 750 ms of inactivity and on field blur.
- Use one single-flight, coalescing mutation queue per `draft_id` generation.
- Later keystrokes remain buffered while a request is in flight and are rebased onto the accepted server response before the next patch.
- Display `Saving`, `Saved`, `Unavailable`, and `Conflict` states.
- `Saved` means the server has acknowledged the exact values currently displayed.
- Ignore delayed responses older than the cached draft generation/version.
- Offline or unavailable copy must explain that other sessions and devices can see only the last server-saved values.

### Draft version conflict

On `ticket_draft_conflict`:

1. Preserve attempted local values in memory.
2. Replace the cached baseline with the returned current server draft/version.
3. Announce that another session changed the draft.
4. Show a field-by-field comparison for Subject, Content, and Urgency.
5. Default each field to the latest server value.
6. Allow the resident to select individual local values to reapply.
7. Submit only selected fields against the returned current version.

Never auto-merge, force-overwrite, or silently retry a conflicting patch. If another conflict occurs, repeat the explicit review while preserving unsent local text.

### Draft generation gone

- On `ticket_draft_generation_gone`, stop the save queue.
- State only that the expected draft is no longer active.
- Link to a ticket only if the response contains a same-account ticket proven by the durable submission record.
- Do not guess whether another session submitted, discarded, or replaced the draft.
- Never apply old-generation edits to a later draft automatically.

### Review and validation

- Review is a state within `/resident/tickets/new`, not a separate route.
- Show read-only resident/location context separately from editable ticket fields.
- Submission is disabled until required fields satisfy frontend assistance checks, but the backend remains authoritative.
- Server validation errors map to an error summary and the relevant fields without discarding entered text.

### Retry-safe submission

- Derive the submission idempotency key exactly as specified in the API contract.
- Store the approved attempt metadata in account-bound `sessionStorage` before sending.
- While `submitting` or `outcome_unknown`, make the submitted fields non-editable and expose an accessible pending-result state.
- Disable repeated submit controls, but do not rely on the disabled button for duplicate prevention.
- After a transport failure, retry the same POST with the same key and fingerprint.
- After a hard reload, confirm the same account with `/auth/me` before restoring and retrying the attempt.
- Clear recovery metadata after definitive success, definitive validation failure, or account switch.
- If browser-session metadata is lost, direct the resident to ticket history rather than guessing the outcome.
- Successful submission shows the created ticket, clears all draft caches, and does not automatically create a new draft.

## 8. Manager Flows

### Work home

- Present direct, accessible entry points to Tickets, Residents, Onboarding, Notifications, and Profile.
- May show limited recent items already returned by approved endpoints.
- Must label partial information honestly and must not calculate full totals from one cursor page.
- Do not add reporting, KPI, SLA, satisfaction, or turnaround widgets.
- A manager with no grants sees a useful empty-scope explanation and can still reach Profile and safe account actions.

### Resident directory and onboarding oversight

- Apply building/floor/unit filters only within backend-returned scope.
- Do not display email, phone, registry ID, or Zalo URL in resident list rows.
- Onboarding rows show only the approved privacy-safe identity/location summary and progress data.
- Resident onboarding details use inline expansion or a drawer when supported by the returned contract; no new resident-detail API may be inferred.
- Managers cannot manually trigger onboarding reminders.

### Ticket queue

- Queue reads, filters, grouping, link previews, and prefetches are side-effect-free.
- Rows display the approved safe fields: ticket ID or safe display identifier, subject, urgency, state, version, submitted timestamp, and immutable building/floor/room snapshot.
- Support grouping or filtering by building, floor, unit, urgency, and state only where allowlisted by the API.
- Navigating to full detail commits the route before calling the open command.

### Ticket detail and open conflict

- Call `POST /manager/tickets/{id}/open` once after authenticated detail navigation commits, using the observed queue/detail status and version plus a stable attempt key.
- `outcome=transitioned` updates `PENDING` to `RESOLVING` and announces the new state without stealing focus.
- `outcome=already_current` displays the current detail without conflict messaging.
- On `ticket_open_conflict`, retain authorized detail, replace stale state/version, announce that another manager opened it first, and expose the persisted conflict notification.
- On protected `404` or `scope_changed`, purge ticket detail, resident/contact data, preview tokens, and related cache entries before routing to a safe manager page.

### Terminal actions

- `Resolved` and `Denied` are available only when allowed by the returned ticket state and capability metadata.
- Both require accessible localized confirmation dialogs.
- `Denied` requires a non-empty explanation before confirmation.
- Confirmation defaults to the safe cancel action.
- On success, update detail and history, announce the result, and keep the outcome visible.
- On `ticket_state_conflict`, keep the page open, replace stale state/version, explain that another manager changed the ticket, and expose the persisted conflict notification.
- The frontend confirmation is UX only; the backend remains responsible for scope, legal transition, version, and denial validation.

### Zalo action

- The action label is exactly `Zalo`.
- Show it on every authorized full ticket detail even when the link is missing or invalid.
- Resolve the destination only through the scoped Zalo endpoint.
- Open a returned URL in a new external context using `noopener`, `noreferrer`, and a no-referrer policy.
- Do not reconstruct, modify, prefetch, or validate existence of the external destination.
- Missing, locally invalid, or pre-handoff navigation failure opens a dialog recommending Notify.
- The dialog must not imply that a notification was sent or that the Zalo profile exists.

### Ticket Notify

- Open a responsive composer drawer or dialog from ticket detail.
- The audience is server-derived from the ticket resident and cannot be edited by the manager.
- Collect trimmed non-empty Subject and Content.
- Request a ticket-specific preview and show the audience summary and recipient count.
- Send only after explicit confirmation using the preview token and a stable idempotency key.
- A stale preview remains unsent and requires a refreshed preview.
- Scope loss closes the composer only after purging preview and resident/contact data.

### Generic notification composer

- Lives within `/manager/notifications` as a page mode or responsive subview.
- Supports the approved audience kinds: Building, Floor, Unit, or selected in-scope Residents.
- Whole-building targeting is offered only when the backend-confirmed scope grants `ALL_FLOORS` for that building.
- The frontend never treats its audience controls as authorization.
- Preview shows the normalized audience summary and recipient count without exposing a bulk contact list.
- Empty resolved audiences cannot be sent.
- `notification_preview_stale` requires review of a refreshed preview; it never silently sends to the new audience.
- `202` means the campaign was durably accepted, not that every recipient has already received or read it.

### Manager notifications and profile

- Manager notifications include ticket conflict notifications and use the same explicit read behavior as resident notifications.
- Profile displays assignments grouped by building with their floors or `ALL_FLOORS` meaning rendered read-only.
- Managers cannot edit building or floor assignments.
- Contact and password changes follow the shared verified account flows.

## 9. Role-Based Route Behavior

- `/auth/me` selects exactly one shell from the backend-confirmed role.
- Client route configuration may omit inaccessible navigation but must not encode authorization truth.
- Direct URLs are sent to the backend and handled using stable capability, not-found, authentication, and scope errors.
- Out-of-scope protected resources use the existence-safe behavior from the API contract; frontend copy must not reveal whether the object exists.
- `scope_changed` purges all manager protected caches and reloads `/auth/me` before any affected resource is rendered again.
- Administrator routes are absent from the MVP build. They are not linked, lazily bundled, or represented by placeholder pages.

## 10. Forms and Client-Side Validation

### Shared behavior

- Use explicit visible labels; placeholders are supplemental.
- Preserve entered values after recoverable errors.
- Trim values only according to the server contract and show the normalized result when it materially changes user input.
- On submit, focus an error summary that links to each invalid field. Do not move focus to the summary on every keystroke.
- Associate help, warning, and error text with fields programmatically.
- Disable only the action whose preconditions are unmet; keep explanations visible.
- Never expose raw backend provider errors, stack traces, secrets, or protected metadata.

### Contract-specific rules

- Registration: username, password, phone, email, role-specific registry ID; backend determines eligibility and OTP destination.
- Ticket: Subject and Content are required after trim; Urgency is `LOW`, `NORMAL`, or `HIGH`.
- Denial: explanation is required, trimmed, and length-limited by the API.
- Notification: Subject and Content are required after trim; audience selection follows the approved selector shapes.
- Zalo: frontend assistance may apply the exact `ZaloLinkPolicy v1`, but backend normalization and validation are final.
- Profile: reject attempts to edit immutable fields in the UI rather than sending them.
- Idempotency keys, CSRF tokens, actor roles, account IDs, snapshot fields, and scope claims are not user-editable form fields.

## 11. Shared Experience States

Every page must define:

- Initial loading
- Background refresh without destructive layout replacement
- Empty state
- Validation or domain error
- Dependency unavailable
- Authentication/session expired
- Permission or scope lost
- Retry state
- Successful result
- Stale data or optimistic conflict where applicable

Rules:

- Important outcomes remain visible in the page or durable history; toasts are supplemental.
- Skeletons approximate the final layout and carry no misleading content.
- Empty states distinguish no data, no scope, no filter matches, and unavailable data.
- Retry controls reuse safe idempotency behavior where required.
- Background refresh never clears current readable data unless continued display would expose revoked scope.
- Error copy uses stable localized product language and may include the request ID for support without exposing internals.

Detailed page states are defined in [`STATE-MATRIX.md`](STATE-MATRIX.md).

## 12. Responsive Behavior

### Breakpoints and reflow

- Minimum product-supported viewport: 360 CSS px.
- Mobile: 360-767 px.
- Tablet/compact manager: 768-1023 px.
- Desktop: 1024-1279 px.
- Wide desktop: 1280 px and above.
- WCAG reflow testing additionally covers 320 CSS px equivalent content width at 400% zoom.

### Resident behavior

- Single-column primary task flow on mobile.
- Read-only resident context and editable ticket fields remain visually distinct without requiring side-by-side layout.
- Draft save state stays close to the editor and remains readable without covering controls.
- Conflict comparison stacks by field on mobile.
- Dialogs that cannot fit comfortably become full-height sheets while preserving dialog semantics and focus management.

### Manager behavior

- Multi-column work layouts are allowed at 1024 px and above.
- Secondary panels collapse at 768-1023 px without hiding primary actions.
- At 360-767 px, queue and detail are stacked routes/views rather than a compressed split pane.
- Tables become cards or responsive rows; all required data and actions remain available.
- Filters use an accessible compact panel or drawer and show active filters outside the drawer.
- Manager terminal, Zalo, and Notify actions remain reachable without horizontal scrolling.

## 13. Accessibility and Keyboard Contract

WCAG 2.2 AA is binding and overrides conflicting optional visual tokens or legacy wireframe behavior.

- Set document language to Vietnamese for the default experience and update it only when actual localized content changes language.
- Provide skip navigation, semantic landmarks, one clear page-level heading, and logical heading order.
- All actions work with keyboard alone and have visible focus.
- Touch targets meet WCAG 2.2 target-size expectations or use documented exceptions.
- Status is never communicated by color alone.
- Dialogs are labeled, trap focus, close through an explicit control and Escape when safe, and return focus to their trigger.
- Live regions announce OTP delivery, validation summaries, draft save outcomes, draft conflicts, ticket open/transition results, notification preview/send outcomes, and scope loss.
- Coalesce autosave announcements to avoid screen-reader noise.
- Respect reduced-motion preferences; no workflow depends on animation.
- Preserve content and function at 200% browser zoom and 400% reflow testing.
- Theme changes preserve text, non-text, focus-indicator, and status contrast.

The existing `DESIGN.md` primary button token pairs white text with light Signal Teal. That pairing must not be implemented where it fails WCAG contrast. Use an accessible token pairing, such as dark Navy text on Signal Teal, while preserving the approved visual direction.

Detailed focus and announcement requirements are in [`ACCESSIBILITY.md`](ACCESSIBILITY.md).

## 14. Reusable Component Boundaries

Required reusable groups:

- Public, Resident, and Manager route shells
- Role-aware navigation driven by backend-confirmed principal data
- Page header, section header, breadcrumbs/back navigation, skip link
- Form field, password field, OTP input, error summary, help/error message
- Loading skeleton, empty state, inline error, retry panel, durable success panel
- Accessible dialog, confirmation dialog, responsive drawer/sheet
- Status badge with text and programmatic label
- Cursor-pagination controls and scoped filter panel
- Notification list/item/read control
- Profile field display and verified-change flow
- Ticket list row/card, ticket timeline, urgency indicator
- Draft editor, save-state indicator, review panel, conflict comparison
- Assistant message, citation, proposal review
- Manager ticket action group, Zalo fallback, notification composer/preview

Components own presentation and interaction mechanics. Feature state owners coordinate API calls, query caches, idempotency keys, versions, and invalidation. Generic visual components must not contain domain authorization or ticket-transition rules.

See [`COMPONENT-MAP.md`](COMPONENT-MAP.md) for detailed ownership.

## 15. Design System and Token Requirements

- Treat the current root `DESIGN.md` as visual direction, subordinate to the PRD, architecture, and WCAG requirements.
- Product name is OnBxrd; legacy MoveIn naming is prohibited.
- Preserve the dark operations-cockpit direction, sparse signal color, flat tonal hierarchy, compact operational density, and explicit human-control emphasis.
- Do not copy legacy wireframe approval states, role switcher, analytics/reporting cards, attachments, or obsolete ticket lifecycle.
- Define semantic tokens rather than using raw colors in feature components: surface, text, muted text, border, focus, primary action, destructive action, warning, success, and each ticket state.
- Provide light/dark theme behavior only to the extent approved by profile preferences and supported tokens. Every theme must meet the same accessibility contract.
- Typography must support Vietnamese diacritics across all required weights.
- Icons require text labels or accessible names and cannot be the sole carrier of status.
- Motion is restrained and task-supporting; reduced-motion disables non-essential transitions.

## 16. Frontend/API Responsibility Boundary

### Frontend owns

- Presentation and responsive layout
- Navigation and route convenience guards
- Accessible forms, dialogs, focus, keyboard operation, and announcements
- Unsaved in-memory draft buffer
- Resume/replace confirmation
- Visible draft and ticket conflict recovery
- Preview/review steps before terminal or notification actions
- Account-bound non-sensitive pending-submit metadata
- Safe API request orchestration, decoding, and cache invalidation

### Backend owns

- Authentication, sessions, CSRF validity, account status, and principal role
- Registry eligibility, OTP validation, verified contacts, and identity claims
- RBAC, manager scope, scope freshness, and existence-safe responses
- Persistent ticket draft, generation, version, validation, and one-draft invariant
- Ticket snapshots, state machine, events, optimistic transitions, and conflict results
- Zalo normalization and rule validation
- Notification audience resolution, preview validity, durable campaigns, and read state
- Onboarding progress, benefit eligibility, assistant grounding, and assistant schema limits
- Idempotency results and audit history

The frontend must never use hidden navigation, disabled buttons, or route guards as proof that an action is authorized.

## 17. API Interaction by Page

Each page uses the API surfaces listed in [`ROUTE-MAP.md`](ROUTE-MAP.md). Cross-cutting requirements:

- Use relative same-origin `/api/v1` URLs.
- Include credentials through the opaque cookie automatically; never read the session token in JavaScript.
- Fetch and attach the session-bound CSRF token to authenticated mutations.
- Attach a correlation/request ID where the shared API client contract requires one.
- Decode stable errors centrally and preserve their machine code for state handling.
- Protect authenticated responses from persistent browser caches.
- Purge protected queries on logout, account switch, `scope_changed`, or protected out-of-scope failure.
- Use cursor pagination and API allowlisted filters; client filters never broaden backend scope.
- Generate or validate TypeScript contracts from OpenAPI.

## 18. Mock API and Frontend-First Development

- Mock at the HTTP boundary using generated/validated API types.
- Keep browser code pointed at the same relative `/api/v1` paths in mock and integrated modes.
- Model stable error codes, cursor pagination, idempotent retries, OTP timing, session expiry, scope changes, and optimistic conflicts.
- Include deterministic fixtures for zero/one active draft, cross-session draft conflict, generation gone, ambiguous submission retry, manager open conflict, ticket transition conflict, Zalo fallback, stale notification preview, and no-scope manager experience.
- Do not include administrator UI fixtures in the MVP frontend package.
- Mock data must be obviously synthetic and contain no real contact data, credentials, tokens, resident identifiers, or raw Zalo links copied from production.
- Do not mock Zalo profile existence or delivery because the product has no such contract.

See [`mock-data/README.md`](mock-data/README.md).

## 19. Frontend Testing Expectations

### Unit and component tests

- Form validation assistance and server-error mapping
- Dialog focus trap/return and safe default actions
- Status text and non-color representation
- Draft single-flight save queue and truthful save labels
- Field-level draft conflict selection and resubmission
- Assistant proposal provenance and replacement review
- Submission idempotency-key derivation against contract fixtures
- Role navigation and administrator-route absence
- Responsive table/card data parity

### Integration tests with mock API

- Resident and manager registration/OTP flows
- Session expiry with same-account and different-account reauthentication
- Direct draft resume versus explicit new-ticket replacement
- Cross-session conflict and generation-gone handling
- Ambiguous submit followed by hard-reload same-key retry
- Resident ticket history/detail after submission
- Manager ticket open transition, open conflict, terminal conflict, and scope revocation
- Zalo success and fallback behavior without delivery claims
- Generic and ticket-specific notification preview, stale preview, accepted send, and retry
- Notification read behavior

### End-to-end and accessibility tests

- Core workflows at 360, 768, 1024, and 1280 CSS px
- Keyboard-only completion of registration, resident ticket submission, manager terminal action, and notification send
- Automated accessibility scans plus manual screen-reader and focus verification
- 200% zoom and 400%/320 CSS px equivalent reflow
- Vietnamese labels, validation, status, and error announcements
- Protected-route behavior and cache purge after logout, account switch, and scope change

Automated passing results are necessary but not sufficient for independent WCAG and acceptance-criteria verification.

## 20. Security-Sensitive Frontend Rules

- Never store passwords, OTPs, session cookies, CSRF tokens beyond the necessary in-memory/request mechanism, provider secrets, or registry credentials in frontend source or persistent storage.
- Never put ticket content, draft content, resident contact data, raw Zalo URLs, or protected IDs into analytics, error-reporting breadcrumbs, URLs, or routine logs.
- Escape untrusted content and render assistant citations without accepting arbitrary executable markup.
- Apply CSP-compatible patterns and avoid inline script dependencies.
- Use `noopener`, `noreferrer`, and no-referrer behavior for Zalo external navigation.
- Purge sensitive caches before redirecting after scope loss or account change.
- Do not use service-worker caching for authenticated HTML, JSON, draft fields, or ticket detail.
- Treat every LLM-proposed field as untrusted input requiring the normal draft validation path.

## 21. Implementation Choices Left to Developer

The Developer may choose, within the approved architecture and this specification:

- Component-library and form-library implementation details
- Query/cache library and generated API-client tooling
- Folder/module naming below the approved route and feature boundaries
- Exact responsive navigation component
- Exact inline-versus-drawer treatment where both are allowed and accessibility is preserved
- Icon set, skeleton styling, and restrained transition timings
- Mock HTTP tooling and test runner integrations
- Internal state-machine representation and idempotency-key utility structure

The Developer may not change routes, actor scope, backend contracts, draft semantics, ticket state behavior, validation authority, security controls, accessibility requirements, or accepted/deferred product scope.

## 22. Readiness

The approved page inventory and behavior are implementation-ready for public, resident, and manager frontend stories, subject to normal story-level acceptance criteria and backend integration dependencies already documented by architecture.

Administrator frontend work remains intentionally deferred. No administrator API or product requirement is removed by this frontend deferral.
