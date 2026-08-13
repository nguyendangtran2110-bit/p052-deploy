# OnBxrd MVP Accessibility Specification

WCAG 2.2 AA is a release requirement for all public, resident, and manager frontend pages. This document adds testable interaction detail to the accessibility contract in [`../architecture/frontend-architecture.md`](../architecture/frontend-architecture.md).

## Coverage

- Public authentication and recovery
- Resident desktop-first flows
- Manager desktop-first flows
- Shared dialogs, drawers, forms, navigation, status, tables/master-detail views, and async feedback
- Vietnamese default content
- Light and Dark themes, including every interactive and semantic state
- Product-supported desktop viewports from 1024 CSS px upward at 100% browser zoom, plus 320 CSS px equivalent reflow at 400% desktop zoom

Administrator frontend accessibility is outside MVP scope because administrator pages are deferred.

## Semantic Structure

- Use semantic `header`, `nav`, `main`, and supporting landmarks.
- Provide a keyboard-visible skip link to the main content.
- Use one descriptive `h1` per page and a logical heading hierarchy.
- Identify multiple navigation landmarks with distinct accessible names.
- Use lists for navigation, notification collections, timelines, and step lists where their relationship is meaningful.
- Use tables only for tabular relationships. Any alternate desktop detail presentation preserves equivalent labels and reading order.
- Do not use clickable generic containers when a link or button is appropriate.

## Language and Vietnamese Content

- Default document language is Vietnamese (`vi`).
- All core navigation, validation, ticket states, notification states, errors, confirmations, and announcements require Vietnamese strings.
- English may be incomplete and must not cause mixed-language controls inside one core task unless a proper localized value is unavailable.
- Fonts must render Vietnamese diacritics without fallback gaps or clipped marks.
- Dates and times are formatted for the active locale while API timestamps remain UTC.
- Do not embed Vietnamese strings inside business logic; use localization keys with variables for safe data.

## Keyboard Contract

- Every interactive element is reachable and operable with keyboard alone.
- Focus order follows the visual and task order.
- No positive `tabindex` values.
- Custom widgets implement the appropriate WAI-ARIA keyboard pattern or use native controls.
- Escape closes non-destructive dialogs and drawers unless doing so would silently lose unsaved work; in that case, show or require the same leave confirmation as the visible close action.
- Enter submits only the intended form and must not bypass review or confirmation steps.
- Space activates buttons and selection controls according to native behavior.
- Sticky controls do not obscure the focused element.
- Focus is never placed inside content hidden by collapsed or conditional layout.

## Focus Management Matrix

| Flow/state | Initial/result focus | Return behavior |
|---|---|---|
| Page navigation | Page `h1` or main content start after route announcement | Browser navigation semantics preserved |
| Login error | Error summary after submit | Error links move to fields |
| Registration OTP sent | OTP stage heading or code field after destination announcement | Back returns to retained safe registration fields |
| OTP invalid/expired | Error summary or code field according to error scope | Resend returns focus to status confirmation |
| Direct draft resume | Draft heading/editor | No replacement dialog |
| Explicit New ticket with draft | Resume/replace dialog; Resume focused | Resume returns to editor; Cancel returns to trigger |
| Replace confirmation | Cancel focused | Cancel returns to Discard and start new trigger |
| Draft conflict | Conflict review heading/first conflicting field | Successful reconciliation returns to editor/status |
| Session expiry | Login heading | Same-account success returns to restored draft context; different account does not |
| Ticket submission error | Error summary | Links move to invalid fields |
| Ticket submission success | Success heading or created-ticket link | Navigation goes to created detail |
| Manager ticket detail open | Detail `h1`; status updates announced without moving focus | Back returns to prior queue position where possible |
| Ticket open conflict | Keep focus in detail heading/status region | No forced move to notification list |
| Terminal confirmation | Cancel focused inside dialog | Cancel returns to action; success moves to updated status heading only if needed |
| Zalo fallback | Dialog heading, then Notify/Cancel controls | Cancel returns to Zalo trigger; Notify moves into composer |
| Notify preview | Preview heading | Back/Edit returns to the first changed/primary composer field |
| Campaign accepted | Durable success heading | Continue action or notification page navigation |
| Scope revoked | Safe destination heading after cache purge | Browser back cannot reveal removed detail |
| Notification read | Preserve list item/position | Related detail navigation follows normal route focus |

## Dialog and Drawer Requirements

- Use an accessible name and, where helpful, description.
- Trap focus while modal.
- Prevent background content from being keyboard or screen-reader interactive.
- Place the safe cancel action first in focus order for destructive, replacement, and terminal confirmation.
- Return focus to the invoking control if it still exists and remains authorized.
- If the trigger was removed because state or scope changed, move focus to the nearest safe page heading/status.
- A desktop drawer or constrained modal retains dialog semantics when it represents a modal flow.
- Nested dialogs should be avoided. Transition from one flow to the next rather than stacking modal focus traps.

## Forms and Errors

- Every input has a persistent visible label.
- Required status is conveyed in text and programmatically.
- Help and error text uses `aria-describedby` or an equivalent relationship.
- Invalid controls expose programmatic invalid state only after validation has run.
- Submit-time error summaries state the number/nature of errors and link to fields.
- Do not move focus for low-level validation on blur unless the user explicitly requests validation.
- Preserve entered values after recoverable errors.
- Password reveal controls announce their state and do not change the input's accessible name unexpectedly.
- OTP entry supports paste, deletion, appropriate input semantics, and screen-reader navigation without one-character auto-focus traps.

## Status and Live Regions

| Event | Priority | Announcement guidance |
|---|---|---|
| Initial page loading | Polite or implicit | Avoid repeated loading announcements for skeleton fragments |
| Registration OTP sent | Polite | State masked destination and expiry; never read full hidden contact |
| Form submit errors | Assertive | Announce summary and error count |
| Draft Saving | Usually silent/polite | Coalesce; do not announce on every keystroke |
| Draft Saved | Polite | Announce only after a pause or explicit blur/save event |
| Draft unavailable | Assertive | State that unsaved values are not yet visible on other devices |
| Draft conflict | Assertive | State that another session updated the draft and review is required |
| Draft generation gone | Assertive | State only that the draft is no longer active |
| Ticket opened as Resolving | Polite | Name the new state without moving focus |
| Ticket open/state conflict | Assertive | State that another manager acted and name the current state |
| Zalo fallback | Dialog announcement | State link unavailable and offer Notify; no delivery claim |
| Notification preview ready | Polite | Announce recipient count and audience summary |
| Preview stale | Assertive | State that nothing was sent and review is required |
| Campaign accepted | Polite | State accepted for processing, not delivered/read |
| Scope revoked | Assertive | State access changed without naming removed protected details |

Use separate live regions or controlled sequencing so simultaneous query and mutation messages do not overwrite each other.

## Color and Contrast

- Normal text meets at least 4.5:1 contrast.
- Large text meets at least 3:1.
- Essential icons, control boundaries, state indicators, and graphical information meet at least 3:1 against adjacent colors.
- Focus indicators meet WCAG 2.2 focus appearance requirements and remain visible in every theme.
- Ticket state, urgency, onboarding state, unread state, error, warning, and success always include text or another non-color cue.
- Do not implement white text on the current light Signal Teal token where it fails contrast. Use a tested dark text pairing or an approved adjusted action token.
- Disabled controls remain legible and are not used as the only explanation for unavailable actions.

### Two-theme contrast contract

- Light and Dark are independently designed and independently tested. Passing Light does not imply Dark passes, and vice versa.
- Test actual semantic pairings from `design/DESIGN.md`: canvas/surface/elevated text, muted text, links, control boundaries, focus, selected, disabled, loading, destructive, status tints, urgency, alerts, overlays, and skeletons.
- Primary, secondary, accent, success, warning, danger, and info foreground pairings use their documented `on-*` foregrounds; do not assume white text is valid on every chromatic token.
- Theme switching preserves state labels, non-color markers, focus visibility, and current/invalid/selected semantics. No component may retain a hardcoded prior-theme value.
- Forced-colors/high-contrast mode preserves native control semantics, focus outlines, current navigation, invalid state, and selected state without relying on background fills.
- Decorative gradients and washes are ignored for contrast calculation; essential content must pass against the underlying solid surface.

## Motion and Timing

- Respect `prefers-reduced-motion`.
- No task requires animation to understand a state change.
- Use only the shared duration/easing tokens in `design/DESIGN.md`; broad use of micro-interaction does not permit arbitrary component timings.
- Under reduced motion, remove page/section/card transforms, stagger, spring, shimmer, attention pulse, theme crossfade, and assistant thinking cycles. Use immediate changes or opacity-only fades no longer than 80 ms.
- Route, dialog, drawer, validation, status, skeleton-to-content, notification-read, ticket-lifecycle, and assistant motion must not delay the next available action or focus placement.
- Protected-data purge, logout/account switch, scope loss, authorization redirect, focus movement, and Zalo external navigation are not animated.
- Avoid auto-advancing content.
- Loading placeholders do not use high-frequency shimmer that causes distraction.
- OTP expiry and resend timing remain readable without requiring rapid action; server timing remains authoritative.
- Toasts do not disappear before important content is available elsewhere.

## Pointer and Target Size

- Ordinary standalone controls and primary actions use a minimum 44 x 44 CSS px target.
- Dense Manager icon/row controls may use 36 x 36 CSS px only when the actual target remains at least 24 x 24, adjacent targets have sufficient spacing, the control has an accessible name, and an equivalent text-labeled action is available where ambiguity would remain.
- Inline links and native text controls may use the WCAG 2.2 spacing/inline exceptions; do not shrink essential icon-only actions below the documented minimum.
- Do not require hover to expose primary actions or essential information.
- Pointer cancellation and confirmation protect terminal, replacement, and send actions.
- Dragging is not required for reordering or completing any MVP task.
- External Zalo opening is initiated only by an explicit user action.

## Desktop Viewport and Zoom Requirements

### 1024 CSS px minimum product viewport

- Resident and Manager core workflows remain usable at 100% browser zoom.
- Navigation, forms, draft editor, conflict comparison, ticket actions, audience controls, and confirmations remain operable by keyboard and pointer.
- Manager tables or master-detail layouts expose all required data and actions.
- Mobile and tablet-specific layouts are not part of the accessibility acceptance scope.

### 320 CSS px equivalent at 400% zoom

- Content reflows into one column except where a two-dimensional data relationship is essential and an accessible alternative is provided.
- No action or status is clipped, overlapped, or hidden.
- Sticky navigation/actions do not consume most of the available content area.
- Focused controls remain visible as desktop browser zoom changes the available content area.

### Text spacing

Pages remain functional when users override line height, paragraph spacing, letter spacing, and word spacing to WCAG test values.

## Desktop Data Availability

For each Manager table/detail or master-detail presentation, tests must confirm access to:

- Resident display name and building/floor/room summary where approved
- Onboarding progress/status fields
- Ticket subject, urgency, state, version/observation data needed for navigation, submitted time, and location snapshot
- Row/detail action
- Pagination and active filters

Required fields and actions remain available throughout the supported desktop range and WCAG zoom/reflow states.

## Screen Reader Scenarios

Manually verify at least:

1. Resident or Manager registration through OTP completion.
2. Direct resident draft resume, autosave, and review.
3. Draft conflict comparison and selective reapply.
4. Ambiguous submission recovery after reauthentication.
5. Resident ticket status history and denied explanation.
6. Manager queue navigation and automatic Resolving announcement.
7. Manager open conflict and terminal confirmation.
8. Zalo fallback into ticket Notify.
9. Notification audience preview, stale preview, and accepted send.
10. Scope revocation and safe-route focus.

Use representative current versions of NVDA with Firefox or Chrome and VoiceOver with Safari where the release environment permits. Automated tooling does not replace this verification.

## Automated Accessibility Checks

- Run an automated accessibility scanner on every page and significant page state.
- Include dialog-open, validation-error, conflict, empty, desktop table/detail, and preview states.
- Test keyboard focus order and focus return with component/integration tests.
- Test accessible names for icon buttons and status controls.
- Test landmark and heading uniqueness.
- Test color tokens in every supported theme.
- Test reduced-motion behavior.
- Test theme switching while focus is inside a dialog, a dirty form, a draft conflict, a loading region, and a Manager data surface.
- Test the pre-paint theme bootstrap for no flash-of-wrong-theme where the selected implementation makes that feasible.

## Accessibility Acceptance Checklist

- All 18 MVP pages have a page title, `h1`, main landmark, and working skip link.
- All controls are keyboard reachable and visibly focused.
- All form errors are programmatically associated and summarized on submit.
- All dialogs trap and return focus safely.
- All important async outcomes are announced and remain visibly available.
- All state and urgency information has a non-color representation.
- Resident and Manager core tasks work at 1024 CSS px and above at 100% zoom, plus required 400% desktop zoom reflow.
- Vietnamese core copy and announcements are present.
- Administrator pages are not included in MVP accessibility scope.
