# OnBxrd MVP Component Map

This document defines reusable frontend boundaries. It does not prescribe a component library, state library, or folder naming convention.

## Boundary Principles

1. Components do not decide authorization. They render capabilities and results returned by feature state owners and the backend.
2. Shared visual components do not call feature APIs directly.
3. Feature controllers own queries, mutations, idempotency keys, optimistic versions, and invalidation.
4. Draft fields have one feature state owner per active `draft_id` generation.
5. Desktop layout and WCAG zoom/reflow variants preserve the same data, actions, labels, and accessibility semantics.
6. Server-returned localized messages are treated as user-safe display content but not as executable markup.

## Application Foundation

| Group | Responsibilities | Must not own |
|---|---|---|
| `ApiClient` | Relative `/api/v1` requests, credentials, CSRF, request IDs, stable error decoding, response validation | Page layout, feature copy, role decisions |
| `SessionProvider` | `/auth/me`, principal, role, account ID, session epoch, scope version, logout/cache purge coordination | Backend authorization or locally invented scope |
| `QueryCacheBoundary` | Account-keyed and scope-keyed cache namespaces, purge on logout/account/scope change | Persistent draft fields or sensitive browser storage |
| `LocalizationProvider` | Vietnamese default strings, formatting, locale-aware dates/numbers, document language | Business rules embedded in translations |
| `ThemeProvider` | Light/Dark semantic tokens, device-default resolution, non-sensitive pre-paint hint, authenticated profile reconciliation, reduced-motion-aware switch transition | Identity/session data in the hint, contrast exceptions, or feature-specific raw colors |
| `ErrorBoundary` | Unexpected rendering failure with request/support context and safe recovery | Raw stack traces in production UI |

## Route Shells and Navigation

| Component group | Responsibilities |
|---|---|
| `PublicShell` | Public page landmark structure and auth-flow navigation |
| `ResidentShell` | Desktop-first resident navigation, New ticket intent, protected content boundary |
| `ManagerShell` | Desktop-first manager navigation and scope-change boundary |
| `PrimaryNavigation` | Renders destinations supplied for the confirmed role; supports keyboard and current-page state |
| `SkipLink` | Moves focus to the main content landmark |
| `PageHeader` | Page title, description, contextual actions, breadcrumbs/back action where needed |
| `ProtectedRouteBoundary` | Waits for session confirmation, handles wrong-role and authentication routing without rendering protected content |

The MVP contains no `AdminShell`, administrator navigation, or administrator route components.

## Shared Feedback and Overlay Components

Visual primitives `PageContainer`, `Section`, `Stack`, `Grid`, `Divider`, `Card`, `Button`, `IconButton`, `Input`, `Textarea`, `Checkbox`, `Radio`, `Switch`, `Badge`, and `StatusIndicator` follow `design/COMPONENT-SYSTEM.md`. They own presentation and native interaction semantics only; feature controllers remain the state/API owners below.

| Component | Responsibilities | Required behavior |
|---|---|---|
| `LoadingSkeleton` | Approximate final layout during initial load | Non-interactive, accessibility-hidden where appropriate |
| `EmptyState` | Distinguish no data, no scope, no matches, and completed states | Provides a relevant next action only when approved |
| `InlineError` | Local recoverable error | User-safe message, request ID when useful, retry action |
| `ErrorSummary` | Form-submit validation summary | Focus on submit failure; links to invalid fields |
| `DurableSuccessPanel` | Keep important results visible | Supplements, not replaced by, a toast |
| `StatusBadge` | Textual ticket/onboarding/notification state | Never color-only; exposes programmatic label |
| `LiveStatus` | Coalesced polite/assertive announcements | Avoid repeated autosave noise |
| `Dialog` | Accessible modal behavior | Label, description, focus trap, Escape policy, focus return |
| `ConfirmationDialog` | Confirm destructive/terminal/replace actions | Safe cancel receives initial focus |
| `DesktopDrawer` | Complex supporting flow in a desktop side panel | Preserves dialog/region semantics and keyboard behavior |
| `ToastRegion` | Supplemental transient feedback | Never sole location of important results |

## Form Components

| Component | Responsibilities |
|---|---|
| `FormField` | Label, control, help, required indicator, error association |
| `PasswordField` | Password entry and optional reveal control with accessible state |
| `OtpInput` | Code entry without forcing one-character focus traps; paste and accessible input semantics |
| `SelectField` | Native or accessible custom selection with full keyboard operation |
| `TextAreaField` | Length guidance and validation without destructive trimming while typing |
| `SubmitButton` | Pending state and duplicate-click protection as UX only |
| `VerifiedFieldDisplay` | Clearly read-only identity/location/contact context |
| `ContactChangeFlow` | Current-password step, new contact entry, challenge state, OTP verification |
| `PasswordChangeFlow` | Current/new password submission and other-session revocation notice |
| `ThemeControl` | Supported account preference without violating contrast requirements |

`DesktopDrawer` is the implementation-boundary name for the visual `Drawer` primitive in `design/COMPONENT-SYSTEM.md`. It may reflow inline or full-width at desktop zoom; `Sheet` is a deferred phone/tablet adaptation, not a separate MVP state owner.

## Authentication Components

| Component/controller | Responsibilities |
|---|---|
| `LoginForm` | Username/password submission and error mapping |
| `RegistrationStepper` | Role choice, role-specific fields, challenge response, OTP verification |
| `MaskedDestinationNotice` | Announce server-selected channel, masked destination, and expiry |
| `OtpChallengeController` | Resend timing, invalid/expired/exhausted/rate-limited states |
| `RecoveryStepper` | Recovery challenge, OTP, and password reset within one page |

## Resident Onboarding and Benefits

| Component | Responsibilities |
|---|---|
| `OnboardingProgress` | Textual overall progress and next required action |
| `OnboardingStepList` | Ordered completed/current/pending/blocked steps |
| `OnboardingStepAction` | Calls only an allowed resident completion action |
| `BenefitList` | Applicable benefits returned by the backend |
| `BenefitCard` | Eligibility, conditions, operating information, and use instructions |
| `BenefitDetail` | Inline/drawer detail without creating a required route |

## Assistant Components

| Component/controller | Responsibilities |
|---|---|
| `AssistantConversation` | Bounded visible conversation context and input orchestration |
| `AssistantMessage` | Grounded answer or explicit unavailable response |
| `CitationList` | Accessible source labels and opaque reference presentation |
| `TicketIntentController` | Resolves active-draft Resume/Replace choice before requesting mutation |
| `AssistantProposalReview` | Compares Subject/Content/Urgency proposals with current draft fields |
| `MissingFieldPrompt` | Shows targeted missing fields without claiming the assistant owns profile data |

Assistant components never receive tools for submission, profile mutation, notification send, or scope mutation.

## Resident Ticket Components

| Component/controller | Responsibilities |
|---|---|
| `ResidentTicketList` | Cursor pagination and list states |
| `ResidentTicketCard` | Subject, urgency, state, submission time, and detail link |
| `ResidentTicketDetail` | Immutable snapshot, current state, denial explanation, event history |
| `TicketTimeline` | Ordered textual lifecycle/events with actor/timestamp data allowed by the DTO |
| `TicketWorkspaceProvider` | One draft generation/version, server baseline, unsaved buffer, save queue, assistant proposal coordination |
| `TicketDraftEditor` | Subject, Content, Urgency editing only |
| `VerifiedResidentContext` | Read-only name, phone, building, floor, and room returned by the backend |
| `DraftSaveIndicator` | Saving, Saved, Unavailable, Conflict truthfully tied to acknowledged values |
| `DraftResumeDialog` | Existing-draft last-updated summary and safe Resume default |
| `DraftReplaceConfirmation` | Explicit second confirmation before atomic replacement |
| `DraftConflictReview` | Per-field server/local comparison and selected-value resubmission |
| `TicketReviewPanel` | Final editable-field and read-only-context review before submit |
| `SubmissionRecoveryController` | Deterministic key, approved `sessionStorage` metadata, same-key retry, hard-reload recovery |
| `SubmissionPendingState` | Non-editable submitting/outcome-unknown experience |

### Ticket workspace ownership rule

Only `TicketWorkspaceProvider` may coordinate draft query data, unsaved buffers, in-flight patches, assistant provenance, and submission state. Individual fields must not start independent draft mutations.

## Notification Components

| Component/controller | Responsibilities |
|---|---|
| `NotificationList` | Cursor list, refresh, and list-position preservation |
| `NotificationItem` | Type/context, timestamp, read state, related-resource action |
| `MarkReadControl` | Idempotent explicit read mutation |
| `NotificationComposer` | Subject, Content, and approved audience selector |
| `AudienceSelector` | Building/Floor/Unit/Residents choices limited to backend-returned scope options |
| `NotificationPreview` | Normalized audience summary, recipient count, expiry/review state |
| `CampaignSendController` | Preview token, send idempotency key, accepted/stale/retry behavior |

`AudienceSelector` improves usability only. It is never an authorization filter and cannot create arbitrary scope combinations.

## Manager Work Components

| Component/controller | Responsibilities |
|---|---|
| `ManagerWorkHome` | Contract-supported navigation and optional limited recent items |
| `WorkAreaCard` | Destination, description, and supported recent-state hint without invented metrics |
| `ScopeSummary` | Read-only building/floor assignments and no-scope state |
| `ScopedFilterPanel` | Allowlisted building/floor/unit/state/urgency filters |
| `DesktopDataList` | Desktop table or master-detail presentation with complete data and actions |
| `ResidentDirectoryRow` | Privacy-safe resident summary only |
| `OnboardingResidentRow` | Privacy-safe identity/location and progress summary |
| `ManagerTicketQueue` | Side-effect-free cursor list and navigation observations |
| `ManagerTicketRow` | Safe ticket fields plus observed state/version for detail open |
| `ManagerTicketDetailController` | Open command, current detail/version, conflict results, cache purge on scope loss |
| `TicketActionGroup` | Zalo, Notify, Resolved, and Denied controls according to returned capabilities |
| `TerminalActionDialog` | Localized confirmation; denial explanation requirement |
| `ZaloAction` | Scoped endpoint call and safe external opening |
| `ZaloFallbackDialog` | Link-unavailable message and Notify entry without delivery claim |
| `TicketNotifyComposer` | Server-preselected resident, preview, and explicit campaign send |

## State Ownership Matrix

| State | Owner | Persistence |
|---|---|---|
| Principal, role, account ID, session epoch, scope version | `SessionProvider` from `/auth/me` | Backend session; memory cache only |
| Collection and detail DTOs | Feature query controller | Query cache only |
| Active draft generation/version/fields | Backend draft API via `TicketWorkspaceProvider` | PostgreSQL; query cache and memory buffer |
| Unsent draft keystrokes | `TicketWorkspaceProvider` | Memory only |
| Pending submit recovery metadata | `SubmissionRecoveryController` | Account-bound `sessionStorage` only |
| Dialog/drawer/open state | Owning page/component | Memory only |
| Notification preview token | Composer controller | Memory only |
| Form field input outside draft | Owning form | Memory only unless backend accepted |
| Theme preference | Backend profile plus `ThemeProvider` | Backend profile; non-sensitive Light/Dark pre-paint hint only in cookie/local storage; memory/cache |

## Desktop Component Contracts

- `DesktopDataList` must prove data/action completeness across supported desktop widths and WCAG zoom/reflow states.
- `DesktopDrawer` may become an inline side panel without changing state ownership.
- Ticket draft conflict fields use a per-field comparison and may compare side by side when space supports it.
- Manager ticket detail may use a desktop split pane or a dedicated detail route.
- Sticky navigation or actions must not cover focused controls or error summaries.

## Component Testing Expectations

- Keyboard and focus behavior for every shared overlay.
- Accessible names and state announcements for status and async feedback.
- Data-completeness snapshots for desktop table/detail representations.
- No API calls from shared presentational components.
- No persistent browser storage of draft fields.
- No administrator components or navigation in the MVP route tree.
- Stable state behavior under duplicate clicks, delayed responses, conflict responses, and account/scope purge events.
