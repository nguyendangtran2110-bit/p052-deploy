# OnBxrd MVP Route Map

This document is the route-level companion to [`FRONTEND-SPEC.md`](FRONTEND-SPEC.md). API paths use the `/api/v1` base defined by [`../architecture/api-contracts.md`](../architecture/api-contracts.md).

## Route Count

| Actor surface | Page count |
|---|---:|
| Public/authentication | 3 |
| Resident | 8 |
| Manager | 7 |
| **Total MVP pages** | **18** |

Administrator frontend routes are deferred and absent from the MVP build.

## Route Resolution Rules

1. Public routes may render without a session.
2. Protected routes call `/auth/me` before rendering role content.
3. `/resident` redirects to `/resident/onboarding`.
4. `/manager` redirects to `/manager/dashboard`.
5. An unauthenticated protected route redirects to `/login` with an allowlisted same-origin return target.
6. A confirmed Resident opening a Manager route returns to `/resident/onboarding` with a capability message.
7. A confirmed Manager opening a Resident route returns to `/manager/dashboard` with a capability message.
8. Administrator paths have no MVP page and resolve through the normal not-found boundary.
9. Route guards are navigation conveniences only. Backend authorization remains mandatory.
10. Protected content is not rendered from stale cache before role, account, session epoch, and manager scope version checks complete.

## Public and Authentication Routes

| Route | Page | Primary APIs | Navigation and state notes |
|---|---|---|---|
| `/login` | Login | `POST /auth/login`, `GET /auth/me`, `GET /auth/csrf` | Links to Register and Recovery. Successful login routes by backend-confirmed role. Session-expired returns focus here. |
| `/register` | Registration and activation | `POST /auth/register/resident`, `POST /auth/register/manager`, `POST /auth/registrations/{challenge_id}/verify` | One user-facing stepper. Role choice selects the backend endpoint. OTP is a page stage, not a route. No administrator option. |
| `/recovery` | Account recovery | `POST /auth/recovery`, `POST /auth/recovery/{challenge_id}/complete` | Challenge, OTP, and password reset remain within one route. Success leads to Login or an authenticated safe landing according to the backend result. |

## Resident Routes

### Resident navigation

Required primary destinations:

1. Onboarding
2. Benefits
3. Assistant
4. Tickets
5. Notifications
6. Profile

`New ticket` is a prominent intent action and is not required to occupy a permanent navigation slot when space is constrained.

| Route | Page | Primary APIs | Page-owned behavior |
|---|---|---|---|
| `/resident/onboarding` | Onboarding | `GET /resident/onboarding`, `POST /resident/onboarding/{step_id}/complete` | Ordered progress, next action, allowed completion, building content links, and no document-upload affordance. |
| `/resident/benefits` | Benefits | `GET /resident/benefits` | Applicable benefit list. Detail opens inline or in a responsive drawer without a required child route. |
| `/resident/assistant` | Building assistant | `POST /resident/chat/messages`, `GET /resident/ticket-draft`, `POST /resident/ticket-draft/start`, `PATCH /resident/ticket-draft` when ticket assistance is active | Grounded Vietnamese answer, citations, unavailable-answer state, and bounded field proposals. Manual ticket entry remains available when the assistant fails. |
| `/resident/tickets` | Ticket history | `GET /resident/tickets` | Cursor list of the resident's tickets. Preserves filters/scroll on detail return where practical. |
| `/resident/tickets/new` | Ticket workspace | `GET /resident/ticket-draft`, `POST /resident/ticket-draft/start`, `PATCH /resident/ticket-draft`, `POST /resident/ticket-draft/replace`, `POST /resident/ticket-draft/discard`, `POST /resident/ticket-draft/submit`, `GET /resident/profile` | One server draft across manual and assistant entry. Direct resume, explicit-new replacement, review, conflict reconciliation, and submission all remain on this route. |
| `/resident/tickets/{ticketId}` | Ticket detail | `GET /resident/tickets/{ticket_id}` | Read-only immutable snapshot, current state, ordered history, and denial explanation. |
| `/resident/notifications` | Notifications | `GET /resident/notifications`, `POST /resident/notifications/{id}/read` | Listing does not mark read. Opening a related item marks read then navigates; items without a destination expand inline. |
| `/resident/profile` | Profile and preferences | `GET /resident/profile`, `PATCH /resident/profile`, `PUT /resident/profile/zalo`, `POST /auth/contact-changes`, `POST /auth/contact-changes/{challenge_id}/verify`, `POST /auth/password/change` | Read-only identity/location, permitted profile edits, verified contact changes, password change, theme, and rule-validated Zalo editing. |

### Resident deep-link behavior

- A direct ticket-detail URL is resolved only by the own-ticket API.
- A direct `/resident/tickets/new` URL resumes the current active draft without a replacement prompt.
- A stale resident ticket identifier receives the backend-safe not-found state.
- A notification related to a ticket uses the opaque related-resource reference; the client does not construct authorization IDs from display data.

## Manager Routes

### Manager navigation

Required primary destinations:

1. Work home
2. Residents
3. Onboarding
4. Tickets
5. Notifications
6. Profile

| Route | Page | Primary APIs | Page-owned behavior |
|---|---|---|---|
| `/manager/dashboard` | Manager work home | `GET /auth/me`; optionally limited recent items from approved manager list APIs | Provides links and honest, contract-supported recent work. No aggregate totals, KPI calculations, reports, or cursor-derived pseudo-metrics. |
| `/manager/residents` | Resident directory | `GET /manager/residents` | Cursor list and allowlisted building/floor/unit filters within current scope. No contact, registry ID, or Zalo data. |
| `/manager/onboarding` | Onboarding oversight | `GET /manager/onboarding` | Scoped progress list. Inline/drawer detail only when supported by returned DTO data. No manual reminder control. |
| `/manager/tickets` | Ticket queue | `GET /manager/tickets` | Side-effect-free cursor list, filters, and grouping. Prefetch must not invoke the ticket-open command. |
| `/manager/tickets/{ticketId}` | Ticket detail and actions | `POST /manager/tickets/{ticket_id}/open`, `POST /manager/tickets/{ticket_id}/transitions`, `GET /manager/tickets/{ticket_id}/zalo`, `POST /manager/tickets/{ticket_id}/notification-previews`, `POST /manager/notification-campaigns` | Route commit precedes the open command. Owns open conflict, terminal confirmation, Zalo fallback, ticket Notify, and scope-revocation handling. |
| `/manager/notifications` | Notifications and composer | `GET /manager/notifications`, `POST /manager/notifications/{id}/read`, `POST /manager/notification-previews`, `POST /manager/notification-campaigns` | Notification inbox plus generic composer page mode. Preview is a state, not a child page. |
| `/manager/profile` | Manager profile | `GET /manager/profile`, `PATCH /manager/profile`, `POST /auth/contact-changes`, `POST /auth/contact-changes/{challenge_id}/verify`, `POST /auth/password/change`, `GET /auth/me` | Shows assignments grouped by building, including `ALL_FLOORS`, as read-only. |

### Manager dashboard data rule

The dashboard may render:

- Navigation cards for each manager work area.
- Current assignment summary from `/auth/me` or Manager Profile.
- A limited recent ticket, onboarding, or notification section from the corresponding approved first cursor page.
- A clear No scope state.

The dashboard must not render:

- Total residents, total tickets, average completion, turnaround time, SLA, satisfaction, trend, or other aggregate metrics without an approved contract.
- Values inferred by counting a partial cursor page.
- Reports or survey results taken from legacy wireframes.

## In-Page States That Are Not Routes

| State/flow | Owning route | Presentation |
|---|---|---|
| Registration OTP | `/register` | Stepper stage |
| Recovery OTP/password reset | `/recovery` | Stepper stages |
| Benefit detail | `/resident/benefits` | Inline expansion or responsive drawer |
| Assistant ticket proposal review | `/resident/assistant` | Inline review panel or accessible dialog |
| Resume or replace active draft | `/resident/tickets/new` | Accessible confirmation dialog |
| Draft field conflict review | `/resident/tickets/new` | Mobile-friendly comparison panel/dialog |
| Ticket review before submit | `/resident/tickets/new` | Page mode/section |
| Contact verification | Resident or Manager Profile | Dialog/stepper tied to profile page |
| Password change | Resident or Manager Profile | Dialog/section tied to profile page |
| Notification detail without resource | Notifications page | Inline expansion/drawer |
| Manager onboarding detail | `/manager/onboarding` | Inline expansion/drawer if DTO supports it |
| Terminal ticket confirmation | Manager ticket detail | Dialog; Denied includes explanation validation |
| Zalo fallback | Manager ticket detail | Dialog recommending Notify without a delivery claim |
| Ticket-specific Notify | Manager ticket detail | Responsive composer drawer/dialog with preview step |
| Generic notification preview | `/manager/notifications` | Composer review state |
| Scope-lost result | Current Manager route | Cache purge followed by safe-route message |

## Navigation Side-Effect Rules

- Route prefetch may call safe GET collection/detail endpoints only where the endpoint has no mutation semantics.
- Manager ticket detail cannot be prefetched through the open command.
- Zalo destinations are fetched only after the user activates `Zalo` on authorized full detail.
- Notification preview is created only after the manager requests Preview.
- Notification send and terminal ticket transitions require explicit activation after review.
- Draft start occurs on explicit New ticket intent or when the direct editor finds no active draft. Merely rendering resident navigation does not start a draft.

## Error and Recovery Destinations

| Condition | Destination behavior |
|---|---|
| Unauthenticated protected request | `/login` with safe return target |
| Wrong confirmed role | Actor's safe landing page |
| Session expired while editing a draft | `/login`; freeze account/epoch-bound unsaved memory until reauthentication result |
| Manager `scope_changed` | Purge protected cache, reload `/auth/me`, then `/manager/dashboard` or current safe list route |
| Protected manager `404` while detail is visible | Purge the protected resource and navigate to `/manager/tickets` or `/manager/dashboard` |
| Resident ticket not found | Remain in resident shell with not-found state and link to `/resident/tickets` |
| Draft generation gone with proven ticket | Offer the proven `/resident/tickets/{ticketId}` destination |
| Draft generation gone without proof | Explain that the draft is inactive; offer Ticket history and explicit New ticket |
| Unknown route | Framework not-found page without protected metadata |

## Route Testing Checklist

- All 18 pages are reachable through intended navigation or direct deep links.
- No administrator route or navigation item is bundled as an MVP page.
- Role navigation is based on `/auth/me`, not client-chosen roles.
- Protected content does not flash before authentication and scope checks.
- Back navigation does not restore purged scope-protected content.
- Manager queue navigation invokes open only after detail route commit.
- Direct resident draft entry resumes without the explicit-new replacement dialog.
- All modal/subview flows remain addressable by page state without creating unapproved routes.
