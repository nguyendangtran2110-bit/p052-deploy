# Product Requirements Document: OnBxrd

**Resident Services Web Application**

- **Owner:** Đào Đức Mạnh
- **Status:** Final - MVP
- **Last Updated:** August 11, 2026
- **Product Authority:** This PRD. `docs/Brief.md` and `PRODUCT.md` are legacy/supporting context only.
- **Primary Language:** Vietnamese required; English optional

---

### Product Authority

This document is the authoritative MVP product specification. Where `docs/Brief.md` or `PRODUCT.md` conflicts with this PRD, this PRD supersedes them. Approved post-MVP deferrals are listed in Section 10 and do not block MVP architecture or implementation planning.

## 1. Product Definition
### Executive Summary

- **Target user & use case**: New homeowners/residents right after unit handover, who need step-by-step onboarding guidance, answers about amenities/regulations, and a way to report and track defects; property management staff who must review and approve every commitment or ticket before it is created.
- **Key differentiator & value proposition**: Unlike scattered manual processes (phone calls, paper checklists, separate channels), OnBxrD combines a stateful onboarding checklist (LangGraph), source-grounded Q&A (RAG over the resident handbook), and structured defect-ticket escalation — all gated by mandatory human approval (HITL) so management retains authority and accountability.
- **Success definition & metrics**: Success means residents complete onboarding faster, defect requests are triaged and resolved accurately, and management spends less time on repetitive questions. Primary KPI: % of residents completing the onboarding checklist within the target window (initial target: 80% within 7 days of handover).

### Product Vision

OnBxrd is a resident-services web application that helps residents onboard into a building, understand the benefits available to them, get reliable answers about building life, request support, and receive relevant communications. It gives building managers a scoped operational view of resident onboarding, tickets, and notifications. A supporting administrator role manages account access and roles.

The chatbot is one capability inside OnBxrd, not the product itself. Human control is centered on resident review and explicit ticket submission, manager-owned ticket handling, and permissioned account and data access.

### Terminology

- **Unit:** the resident's apartment or room. Product copy may use the locally appropriate term.
- **Validated Zalo link:** a resident-provided value that passed local `ZaloLinkPolicy v1` structural checks. Validation does not prove that the profile exists or belongs to the resident.

### Product Thesis

Residents should not need to assemble their building experience from scattered documents, informal messages, and repeated calls to management. Managers should not need to manually find resident contact details, triage unstructured requests, or sort through tickets outside their real-world responsibilities.

OnBxrd creates one traceable workflow for:

- guided onboarding;
- resident benefits and entitlements;
- approved building information;
- manual and chat-assisted ticket creation;
- manager ticket processing and resident contact;
- resident and manager profiles;
- targeted notifications; and
- account and role administration.

### Product Principles

1. **Resident-controlled submission:** the chatbot may prepare a ticket, but only the resident submits it.
2. **One ticket workflow:** direct form entry and chatbot assistance update the same persistent account draft and use the same validation.
3. **Vietnamese first:** all core workflows must work naturally in Vietnamese.
4. **Verified and scoped access:** identity and role alone are insufficient; managers access only their assigned buildings and floors.
5. **Approved information only:** the chatbot does not invent unsupported building guidance.
6. **Configurable operations:** onboarding steps, benefits, and communication audiences evolve without redesigning the product.
7. **Relevant communication:** reminders and notifications reduce confusion without creating avoidable message noise.
8. **Safe external contact:** resident-provided Zalo links are validated before authorized managers can open them.

---

## 2. Problem Statement and Goals

### Resident Problems

Residents may not know:

- which move-in steps are required or incomplete;
- how to join official building communication channels;
- which facilities, services, and benefits they are eligible to use;
- where to find current regulations and building instructions;
- how to submit a complete support request;
- how a ticket is progressing; or
- whether a management message applies to their building, floor, unit, or only them.

### Manager Problems

Managers need to:

- see onboarding progress only for residents within their responsibilities;
- receive and process tickets only from their assigned buildings and floors;
- avoid manually searching for a resident's Zalo profile;
- contact a resident through Zalo or an OnBxrd notification;
- send targeted notices without reaching unrelated residents; and
- preserve a traceable history of ticket and notification actions.

### Product Goals

- Make onboarding progress visible and actionable for residents and assigned managers.
- Make resident benefits discoverable based on verified resident identity.
- Provide reliable Vietnamese answers from approved building information.
- Let residents create complete tickets manually or with chatbot assistance.
- Keep ticket submission under resident control.
- Limit manager visibility and actions to profile-assigned buildings and floors.
- Give managers direct, safe access to a resident-provided, validated Zalo profile link from a ticket.
- Deliver targeted, auditable OnBxrd notifications.
- Prevent outsiders and out-of-scope staff from accessing resident data.

### Non-Goals for the First Release

- The chatbot does not submit tickets automatically.
- Managers do not approve tickets before resident submission.
- Managers cannot change their own building or floor assignments.
- Managers do not manually trigger onboarding reminders.
- Live Zalo group ingestion, group monitoring, message reading, and automated Zalo messaging are not included.
- Live Zalo API access, profile-existence checks, and profile-ownership verification are not included.
- The Zalo button does not prove that an external message was sent, delivered, or read.
- Anonymous users do not receive persistent ticket drafts.
- English-language parity is not required.

---

## 3. Product Actors and Access Model

### Resident

A verified building resident who uses OnBxrd during move-in and throughout their stay. A resident can access only their own profile, onboarding progress, benefits, tickets, and notifications.

### Manager

A building-management staff member with an account-specific profile. The profile contains one or more assigned buildings and the floors assigned within each building. A manager may cover multiple buildings and different floors in each building.

Manager assignments determine which residents, onboarding records, tickets, ticket alerts, and notification audiences the manager can access. Managers can view their assignments but cannot change them in OnBxrd.

### Administrator

A privileged support role responsible for account lifecycle and role administration. The first release supports account creation or invitation, deactivation, restoration, recovery assistance, identity-correction assistance, role assignment, and resident building/unit association. Administrator access to conversations, documents, tickets, and manager scope assignment remains subject to explicit policy decisions.

### Access Invariants

- A building-issued resident identifier is a lookup key, not sufficient authentication by itself.
- Every request is authorized using the authenticated account, role, and applicable resident or manager scope.
- Out-of-scope managers cannot discover, list, open, contact, or notify a resident outside their assignments.
- Manager scope is evaluated as exact building-floor pairs; floors assigned in one building do not grant access to the same floor number in another building.
- A manager receives scope only for building-floor assignments present on their profile; a building assignment with no assigned floors grants no resident scope.
- Direct URLs and API identifiers do not bypass scope checks.
- Unauthorized responses do not reveal whether a resident, ticket, or resident Zalo link record exists.

---

## 4. Core User Journeys

### UJ-1: Resident Account Activation and Onboarding

A resident enters a building-issued resident identifier and completes an additional verification step. On successful activation, OnBxrd associates the account with the correct resident, building, floor, and unit. The resident sees an onboarding plan containing required and completed steps, beginning with account activation and an official Zalo group join link. Additional documentation and building-specific steps are added as requirements become known.

### UJ-2: Resident Benefit Discovery

The resident opens their benefits area and sees facilities, services, and entitlements applicable to their verified identity. Each item explains eligibility, conditions, operating details, and the action needed to use it.

### UJ-3: Ongoing Building Assistant

The resident asks a Vietnamese question about onboarding, benefits, regulations, rules, or facilities. The chatbot answers from approved building information and identifies the source. When approved information does not support an answer, it says the information is unavailable rather than inventing guidance.

### UJ-4: Manual Ticket Creation

The resident opens the ticket form. OnBxrd loads the one active draft for that authenticated account, or creates one if none exists. Verified profile fields such as name, unit, and phone number are prefilled read-only. The resident completes the remaining required fields, reviews the form, and explicitly submits it. The submitted ticket enters `Pending` and the active draft is cleared atomically.

### UJ-5: Chat-Assisted Ticket Creation

The resident describes an issue in chat. The chatbot proposes updates to the same persistent account draft used by the ticket form, extracts known fields, and asks for missing required information. Existing resident-entered values are preserved unless the resident confirms a proposed replacement. The resident is routed to the ticket page to review and submit. If a draft already exists, starting a new ticket flow offers `Resume draft` or an explicitly confirmed replacement.

### UJ-6: Manager Ticket Processing and Contact

The manager sees a ticket queue limited to assigned buildings and floors and organized by building, floor, and unit. The manager can view ticket details, use the resident's structurally validated Zalo link or the OnBxrd notification fallback, and perform only the lifecycle actions allowed by the approved ticket contract. Opening full detail automatically changes a `Pending` ticket to `Resolving`.

### UJ-7: Manager Onboarding Oversight

The manager sees onboarding progress only for residents in assigned buildings and floors. OnBxrd sends automated reminders according to configured timing while onboarding is incomplete. The manager has no manual reminder control.

### UJ-8: Targeted Manager Notification

The manager composes a notification with a subject, content, and audience. The available audience is limited to assigned buildings and floors and may be narrowed to a floor, unit, or selected in-scope residents. OnBxrd shows an audience preview before sending and retains an audit record.

### UJ-9: Account Administration

An administrator creates or invites an account, assigns a role, binds a resident to the correct building and unit, assists with recovery, or deactivates/restores access. Elevated content access is not implied by the administrator role unless explicitly approved.

---

## 5. Functional Requirements

### 5.1 Account Activation and Authorization

#### FR-ACC-001: Secure Resident Activation

Residents can create or activate an account using a building-issued resident identifier plus additional verification.

Acceptance criteria:

- The resident identifier must match an authorized resident record.
- The identifier alone cannot activate or authenticate an account.
- Successful activation binds the account to the correct resident, building, floor, and unit.
- Failed activation uses a generic response that does not expose resident-registry data.
- Recovery and correction flows do not silently change verified identity data.

#### FR-ACC-002: Role and Scope Enforcement

OnBxrd enforces resident, manager, and administrator permissions at the backend trust boundary.

Acceptance criteria:

- Residents can access only their own data.
- Managers can access only residents and tickets in profile-assigned buildings and floors.
- Administrators receive only explicitly granted administrative capabilities.
- Client-provided role or scope values cannot grant access.
- Out-of-scope direct requests are denied without returning protected object metadata.

#### FR-ACC-003: Manager Profile and Assignments

Each manager has a profile showing assigned buildings and the assigned floors within each building.

Acceptance criteria:

- A manager can have multiple building assignments.
- Each building assignment can contain a different set of floors.
- Authorization evaluates the assigned building-floor pairs without combining independent building and floor lists.
- A building assignment with no assigned floors grants no resident scope.
- Assignments are displayed read-only to the manager.
- Resident lists, onboarding views, ticket queues, ticket alerts, and notification audiences use the current assignments.
- After OnBxrd applies an updated assignment record, all scoped views and actions use that updated scope.
- Managers do not need to edit account settings for an externally decided assignment change to take effect.

#### FR-ACC-004: Administrator Account Lifecycle

Authorized administrators can create or invite, deactivate, restore, and assist with recovery or verified identity correction for resident, manager, and administrator accounts.

Acceptance criteria:

- Deactivated accounts cannot authenticate.
- Restoring an account preserves its identity and authorized history.
- Identity corrections preserve an audit record of the prior and corrected association.
- Role changes and account lifecycle actions are audited.
- Permanent deletion and administrator access to product content are not enabled without explicit policy approval.

### 5.2 Guided Onboarding

#### FR-ONB-001: Configurable Onboarding Plan

Residents receive a persisted onboarding plan with ordered steps and progress.

Acceptance criteria:

- Residents can distinguish completed, current, pending, and blocked steps where applicable.
- Progress persists across sessions.
- The plan shows the next required action.
- Authorized configuration can add, reorder, revise, or retire steps without redesigning the resident experience.
- Initial supported content includes account activation and an official Zalo group join link.
- Documentation steps remain configurable until the required documents and evidence rules are approved.

#### FR-ONB-002: Automated Onboarding Reminders

OnBxrd automatically reminds residents about incomplete onboarding.

Acceptance criteria:

- Reminder scheduling begins when the resident account is created and can receive OnBxrd notifications, according to configured timing.
- Reminders repeat only at approved intervals while required steps remain incomplete.
- Completion stops future onboarding reminders.
- Managers cannot manually send onboarding reminder actions from the progress view.
- Duplicate reminders for the same interval are prevented.

#### FR-ONB-003: Scoped Manager Progress View

Managers can view onboarding progress for in-scope residents.

Acceptance criteria:

- The view includes only residents in assigned buildings and floors.
- Managers can identify incomplete and blocked steps.
- Managers cannot access progress through direct links after scope removal.
- Progress reflects the resident's persisted state.

### 5.3 Benefits and Entitlements

#### FR-BEN-001: Resident Benefit Directory

Residents can see benefits available to them based on verified identity and building context.

Acceptance criteria:

- Residents see only applicable benefits.
- Each benefit states eligibility, conditions, operating information, and how to use it.

#### FR-BEN-002: Configurable Benefit Content

An approved content-management role can maintain benefit content and applicability without a product redesign or code change.

Acceptance criteria:

- Authorized users can create, revise, and retire benefit records through an approved content-management process.
- Benefit records can be scoped by building and by approved resident-eligibility attributes.
- Changes do not retroactively alter the audit history of benefit information previously presented to residents.
- The responsible maintenance role, approval workflow, effective-date rules, and expiry behavior remain subject to the benefit-governance decision in Section 10.

### 5.4 Vietnamese-First Resident Assistant

#### FR-CHAT-001: Grounded Building Questions

The chatbot answers questions about onboarding, benefits, regulations, rules, facilities, and other approved building information.

Acceptance criteria:

- Core questions and responses work in Vietnamese.
- English support may be incomplete without blocking the first release.
- Supported answers use approved information for the resident's building.
- Supported answers show a source reference.
- Unsupported questions receive an explicit unavailable-answer response rather than invented guidance.

#### FR-CHAT-002: Ticket Draft Assistance

The chatbot can create or update a resident ticket draft.

Acceptance criteria:

- The chatbot and direct form operate on the same draft.
- The chatbot extracts supported ticket fields from the conversation.
- Missing required fields produce targeted follow-up questions.
- The chatbot may propose values only for `Subject`, `Content`, and `Urgency`, using the conversation. Resident name, phone number, building, floor, and room are backend-filled read-only fields and are never chatbot-owned draft fields.
- Existing resident-entered values are not overwritten without confirmation.
- A proposal is tied to the draft generation/version observed when it was produced; if that draft changed before the response arrives, the resident must review the proposed replacements before they are applied.
- Chat extraction cannot replace controlled verified identity or location fields; those changes use the verified correction flow.
- The chatbot cannot submit the ticket.

### 5.5 Ticket Creation and Lifecycle

#### FR-TKT-001: Canonical Ticket Draft

Every ticket begins as one resident-controlled persistent draft for the authenticated resident account, regardless of entry path.

Acceptance criteria:

- Manual and chatbot entry use the same required fields and validation rules.
- Verified resident profile fields are prefilled read-only by the backend.
- Each authenticated resident account has zero or one active ticket draft at a time across all of its sessions and devices.
- The draft is stored server-side and survives refresh, logout/login, and switching devices or browsers for the same account.
- Anonymous users cannot create or persist an account draft.
- The current draft is shared when the resident moves between chat and the form or uses another authenticated session.
- Direct entry to the active ticket editor, refresh, login recovery, and route/device continuation resume the saved draft without a replacement prompt. An explicit `New ticket` intent, or an assistant request to start a new ticket, presents `Resume draft` and an explicit `Discard and start new` choice; resume is the safe default.
- Replacing a draft atomically changes the existing account-owned draft generation in its single slot and never creates a second active draft.
- The resident can review and edit permitted fields before submission.
- Chatbot-proposed changes do not silently overwrite resident-entered values.
- Concurrent draft updates detect stale state, return the current saved draft for reconciliation, and never silently overwrite an accepted update.
- Concurrent sessions use an immutable draft generation identifier plus an optimistic version; a stale generation cannot update a later draft even when version numbers repeat.
- A submitted ticket cannot be mutated by later edits to a cleared draft.
- Successful submission clears the active draft in the same transaction as ticket creation.
- There is no inactivity expiry in MVP. Logout, session expiry, and deactivation do not delete the draft; a deactivated account cannot access it until restored. Permanent account deletion/cleanup is outside MVP.

#### FR-TKT-002: Resident Submission

A ticket is created only after the resident explicitly submits the reviewed form.

Acceptance criteria:

- Submission is blocked until required fields pass validation.
- Successful submission creates a ticket in `Pending`.
- Successful submission clears the account's active draft atomically with ticket creation.
- The resident receives confirmation and can open the ticket from history.
- Management approval is not required before ticket creation.
- Duplicate submission caused by repeated clicks or retries is prevented.

#### FR-TKT-003: Ticket Lifecycle

The first release uses four resident-visible ticket states: `Pending`, `Resolving`, `Resolved`, and `Denied`.

Acceptance criteria:

- Successful resident submission creates the ticket in `Pending`.
- Only an authorized in-scope manager can perform a manager-owned status transition.
- Opening full ticket detail by an authorized manager automatically changes `Pending` to `Resolving`; queue/list reads and later views of an already `Resolving` ticket do not create another transition.
- `Resolved` and `Denied` are terminal states in MVP.
- Both terminal actions require a confirmation step; only `Denied` requires a non-empty explanation.
- Residents can see current status and status history.
- Every status change records the authenticated manager and timestamp.
- Opening Zalo or sending an OnBxrd notification does not change ticket status.
- Concurrent opens and terminal status changes use first-valid-write-wins behavior; losing managers receive an OnBxrd notification.
- A denied ticket displays the manager-provided explanation to the resident.
- A resolved ticket does not require a completion note in MVP.

#### FR-TKT-004: Scoped Manager Ticket Queue

Managers receive and view only tickets within profile assignments.

Acceptance criteria:

- Ticket lists are restricted to assigned buildings and floors.
- The queue can be grouped or filtered by building, floor, and unit.
- Ticket alerts are sent only for in-scope tickets.
- Opening a direct URL for an out-of-scope ticket is denied.
- After an updated assignment is applied, removed scope no longer grants ticket access; the refresh and revocation timing is defined by the assignment contract.

#### FR-TKT-005: Resident Zalo Profile Contact

An authorized manager can open the ticket resident's validated, resident-provided Zalo profile link from the ticket detail.

Acceptance criteria:

- The action label is exactly `Zalo`.
- The `Zalo` action is visible to an authorized in-scope manager for every ticket.
- Selecting `Zalo` opens the validated resident-provided profile link when one is available.
- When no validated link is available, selecting `Zalo` shows a popup recommending contact through an OnBxrd notification.
- OnBxrd does not control which Zalo account is currently logged in.
- OnBxrd does not claim that a message was sent, delivered, or read.
- The action does not change ticket status or assignment.
- The destination is resolved from the ticket resident; the client cannot substitute an arbitrary URL or resident.
- The action is unavailable to residents, unauthenticated users, and out-of-scope managers.
- The launch attempt is audited without storing the raw Zalo URL or message content in routine logs.

#### FR-TKT-006: Zalo Link Validation and Fallback

Resident-provided Zalo profile links are validated before manager use.

Acceptance criteria:

- Rule-based validation uses the versioned `ZaloLinkPolicy v1` contract: `https://zalo.me/<profile-id>` only, with one ASCII `[A-Za-z0-9._-]{1,128}` path segment (optional trailing slash), no user-info, explicit port, query, fragment, encoded separators, or control characters. The policy and fixtures are version-controlled with the architecture.
- Non-Zalo, malformed, script, data, or otherwise unsafe links are rejected.
- Validation is structural only; OnBxrd does not call Zalo or another external service to verify that the profile exists.
- Editing or replacing a link triggers the same local structural validation again.
- A missing or locally invalid link keeps the `Zalo` action available as a fallback affordance and shows the popup when selected.
- If navigation is blocked or fails before the external service takes control, the manager receives the same explicit popup fallback.
- OnBxrd does not infer whether the Zalo application or profile actually opened after control passes to the external service.
- The popup does not imply that an OnBxrd notification was sent until the manager explicitly sends one.
- A notification started from this fallback is pre-scoped to the ticket resident and rechecks manager scope before it can be sent.
- External profile-existence verification and ownership proof are deferred post-MVP.

### 5.6 Profiles, Preferences, and History

#### FR-PRO-001: Resident Profile

Residents can view their profile, ticket history, and permitted preferences.

Acceptance criteria:

- Residents can edit explicitly permitted contact and preference fields.
- Residents can change the UI theme.
- Verified resident identity, building, floor, and unit fields use a controlled correction flow.
- A Zalo profile link can be added or changed only through the validation flow.
- Residents can see their own ticket history and current ticket statuses.

#### FR-PRO-002: Manager Profile

Managers can view their profile and access assignments.

Acceptance criteria:

- The profile displays the manager's identity and access assignments.
- Assignments are grouped by building.
- Each building shows the floors assigned to the manager.
- The profile supports managers assigned to more than one building.
- Managers cannot edit building or floor assignments.

### 5.7 Notifications

#### FR-NOT-001: Resident Notifications

Residents receive relevant OnBxrd notifications.

Acceptance criteria:

- Supported categories include ticket updates, manager messages, management announcements, onboarding reminders, and documentation, credential, or account-verification issues.
- Notifications identify their category and relevant context.
- Important results remain visible in notification history rather than existing only as transient toasts.

#### FR-NOT-002: Targeted Manager Notifications

Managers can send OnBxrd notifications to authorized audiences.

Acceptance criteria:

- A notification includes a trimmed, non-empty subject and content.
- Available audiences are limited to assigned buildings and floors.
- Managers may narrow the audience to an assigned floor, unit, or selected in-scope residents.
- Managers cannot target or discover out-of-scope residents through audience controls.
- The interface shows an audience summary and recipient count before sending.
- Sending is blocked when the resolved audience is empty.
- Scope and recipients are re-evaluated at send time; if the preview is no longer valid, sending is blocked until the manager reviews a refreshed non-empty preview.
- The audit record stores the sender, audience definition, resolved recipient set, send time, and send result, subject to the approved retention policy.

---

## 6. Data and Integration Requirements

### Core Data

The product requires persistent records for:

- accounts, roles, and account status;
- resident profiles and verified building/floor/unit associations;
- manager profiles and per-building floor assignments;
- buildings, floors, and units;
- onboarding definitions, steps, and resident progress;
- benefits and eligibility data;
- approved knowledge-source references returned with chatbot answers;
- zero or one active account-owned ticket draft per authenticated resident, tickets, and ticket events;
- resident Zalo links and local rule-validation state;
- notifications, audience definitions, resolved recipients, send results, and history;
- knowledge-source documents and versions; and
- security and operational audit events.

### Required Product Contracts

- Resident activation and additional verification.
- Manager-assignment import or update from the approved assignment source.
- Resident and manager profile retrieval.
- Onboarding definition, progress, and reminder scheduling.
- Benefit eligibility and content retrieval.
- Grounded chatbot query and source response.
- Single account ticket-draft start/resume/replace/update/discard/submit.
- Resident ticket submission and manager status transitions.
- Scoped ticket, resident, onboarding, and notification queries.
- Rule-based Zalo-link validation and safe redirect resolution without profile-existence verification.
- OnBxrd notification composition, audience preview, send, and audit history.
- Administrator account lifecycle and role operations.

### Integration Boundaries

- The official Zalo group join link is building-level onboarding content.
- A resident Zalo profile link is personal profile data and is stored separately from the group link.
- The `Zalo` action launches an external profile; OnBxrd does not read or automate the resulting conversation.
- MVP does not require Zalo API access or any external profile-existence call. Existence/ownership verification is deferred post-MVP.
- The exact source and update method for real-world manager assignments requires an approved contract.

---

## 7. User Experience Requirements

### Resident Experience

- Web-based navigation exposes onboarding, benefits, chatbot, tickets, profile, and notifications as distinct but connected tasks.
- Chat and ticket form transitions load and update the same persistent account draft.
- When an active draft exists, starting ticket creation shows its last-updated summary and offers `Resume draft` or an explicitly confirmed `Discard and start new`; resume is the default focused action.
- Draft save state is visible as saving, saved, unavailable, or conflict. A conflict never silently overwrites another authenticated session's accepted update.
- Profile-prefilled fields and chatbot-filled fields are distinguishable when necessary for review.
- Residents always reach a reviewable ticket page before submission.
- Vietnamese is the default core experience.

### Manager Experience

- The manager profile makes building and floor scope visible.
- Resident, onboarding, ticket, and notification surfaces apply the same scope consistently.
- Ticket queues support building, floor, and unit organization to reduce operational clutter.
- Ticket detail presents `Zalo`, OnBxrd notification, and lifecycle actions as separate controls.
- Viewing, contacting, and changing status are visibly different actions.

### Required States

Relevant surfaces include visible loading, empty, unavailable, validation-error, permission-denied, and retry states. Status cannot rely on color alone. Important outcomes remain visible on the page or in history; toasts are supplemental.

### Desktop UX and Accessibility Baseline

WCAG 2.2 AA is required. Resident-facing and manager-facing flows are desktop-first. The minimum product-supported viewport is 1024 CSS px at 100% browser zoom, with layout targets at 1024, 1280, and 1440 CSS px and above. Mobile and tablet-specific navigation, compact layouts, touch or virtual-keyboard optimization, and product acceptance testing below 1024 CSS px at 100% zoom are out of scope. Keyboard operation, meaningful labels, visible focus, accessible dialogs, screen-reader-readable status changes, 200% zoom, and WCAG reflow at 320 CSS px equivalent content width remain required desktop accessibility behavior; reflow compliance does not create a mobile-support commitment.

---

## 8. Non-Functional Requirements

### Security and Privacy

- Authenticate every protected action using the server-validated account principal.
- Apply role and manager profile scope to every protected resident, ticket, onboarding, and notification operation.
- Validate all external Zalo links locally using allowlisted patterns and safe URL handling; do not perform profile-existence calls in MVP.
- Do not expose raw Zalo URLs, phone numbers, tokens, or protected resident identifiers in routine logs.
- Audit account lifecycle, role changes, manager scope changes, ticket transitions, Zalo launches, and notification sends.
- Protect verified identity fields from unrestricted editing.
- Define retention and deletion policies before collecting onboarding documents or other sensitive uploads.

### Reliability

- Preserve the one active account ticket draft across chat/form navigation, refresh, logout/login, and authenticated devices/browsers.
- Reject stale draft updates using optimistic version checks so concurrent sessions cannot overwrite accepted changes or create multiple active drafts.
- Prevent duplicate ticket submission and duplicate scheduled reminders.
- Fail safely when approved knowledge, manager assignments, or notifications are unavailable. Zalo structural validation has no external availability dependency.
- Never claim external Zalo message delivery based on link launch.

### Performance

- No quantitative performance acceptance criteria are approved yet.
- The pilot load model must define expected resident, manager, building, ticket, notification, and concurrent-session volumes.
- Architecture-defined functional, concurrency, recovery, and scoped-list checks apply to MVP stories. Quantitative latency, availability, capacity, and performance targets remain deferred post-MVP and are not an implementation gate for MVP stories.

### Localization

- Vietnamese is required for navigation, validation, core chatbot behavior, ticket flows, statuses, notifications, and error states.
- English is optional and may be introduced incrementally.

---

## 9. Success Signals and Analytics

Numeric targets will be set after baseline data, pilot population, and measurement definitions are approved.

### Resident Success Signals

- Onboarding completion and time to completion.
- Reduction in manager intervention needed to complete onboarding.
- Benefit discovery and benefit-use actions.
- Successful resolution of approved-information questions.
- Complete ticket submission through manual and chat-assisted paths.
- Resident visibility into ticket status and manager responses.

### Manager Success Signals

- Percentage of manager views and actions correctly limited to assigned scope.
- Time tickets remain in `Pending` and `Resolving`.
- Ticket outcomes by building, floor, category, and status.
- Reduction in time spent locating resident contact information.
- Successful Zalo profile launches and use of OnBxrd notification fallback.
- Notification send results and targeting accuracy.

### Safety and Quality Signals

- Unsupported chatbot questions correctly receive the approved unavailable-answer response.
- Unsafe or invalid Zalo links rejected.
- Unauthorized resident, ticket, and notification access attempts denied.
- Duplicate tickets and duplicate reminder events prevented.
- Manager assignment updates are applied within the approved update window and revoked access is no longer usable.

### Required Measurement Definitions

Before targets are approved, the team must define denominators, measurement windows, baselines, owners, data sources, and counter-metrics for each selected KPI.

---

## 10. MVP Decisions and Approved Deferrals

### Resolved MVP Decisions

- Resident and manager self-registration uses a matching registry identity/contact plus OTP; administrators have no public registration path.
- Ticket fields are subject, content, urgency, and backend-derived resident/location snapshots.
- Each authenticated resident account has zero or one persistent active ticket draft; while a draft exists it is the account's single shared draft across sessions and devices.
- Full ticket detail automatically changes `Pending` to `Resolving`; `Resolved` and `Denied` are terminal, both require confirmation, and only `Denied` requires an explanation.
- Ticket history uses immutable submitted resident/location snapshots and current manager scope.
- Resident/manager username and registry ID are immutable; resident location and manager assignments are administrator/registry controlled.
- Zalo validation is local and rule-based only; no profile-existence or ownership request occurs in MVP.
- WCAG 2.2 AA and desktop-first resident and manager behavior are approved. The supported product viewport begins at 1024 CSS px at 100% zoom; mobile and tablet UX/UI are explicitly outside MVP scope, while WCAG zoom and reflow remain required accessibility behavior on desktop.

### Approved Deferred Post-MVP Items

- Benefit and chatbot-source governance.
- Notification type catalog and retention.
- Manager-registry maintenance ownership/workflow.
- KPI and quantitative performance targets.
- Document uploads and retention/security controls.
- External notification channels and live Zalo messaging, including profile-existence or ownership verification.
- Ticket attachments, categories, reopening, cancellation, escalation, and SLAs.

These deferrals do not block MVP architecture or implementation planning. Implementations must not silently introduce the deferred capabilities or policies.

---

## 11. Risks and Mitigations

- **Resident impersonation:** a guessable resident identifier could expose data. Mitigate with additional verification, rate limits, and generic failure responses.
- **Manager overreach:** stale or incorrect assignments could expose residents and tickets. Mitigate with backend scope enforcement, an approved assignment-update contract, audit, and rapid revocation.
- **Malicious Zalo links:** unsafe resident input could target managers. Mitigate with rule-based allowlisting, revalidation, and safe redirect resolution; structural validation does not claim profile existence.
- **False contact claims:** opening Zalo does not prove communication or even prove that the external application opened successfully. Mitigate by reporting only the OnBxrd handoff attempt and preserving OnBxrd notification as a separate action.
- **Ticket draft conflicts:** multiple authenticated sessions could overwrite resident intent. Mitigate with one account-unique draft row, optimistic version checks, idempotent mutations, visible conflict recovery, and confirmation before replacement.
- **Notification noise or leakage:** broad or repeated messages could reach the wrong residents. Mitigate with scope enforcement, recipient preview, scheduling controls, deduplication, and audit.
- **Stale building information:** outdated sources could produce incorrect guidance. Mitigate with accountable source owners, versioning, and explicit refusal when approved information is unavailable.
- **Incorrect benefit eligibility:** residents could see benefits they cannot use. Mitigate with building-scoped eligibility rules and the approved benefit-governance process.
- **Unbounded administrator access:** support privileges could expose resident data. Mitigate with explicit capabilities, least privilege, and audited elevation.

---
### Demo UI Surface

- **Landing**: Boomerang positioning and direct links into the working surfaces. Booking, purchasing, and unrelated conversion actions are intentionally excluded from the demo.
- **Onboarding**: A resident checklist with step-by-step agent guidance, grounded answers with source references, and a resident context summary.
- **In-app chat**: A resident conversation inside the OnBxrD app for handbook Q&A and maintenance issue intake. The agent detects ticket intent, collects the structured fields, and asks for confirmation before creating a ticket.
- **Ticket**: A resident ticket workspace with a dedicated one-to-one conversation. The resident reviews the structured request before submission, then sees status events and follow-up messages in the same ticket thread.

---

## 12. Implementation Readiness

This PRD is the authoritative final MVP product specification. Architecture, UX, API/data contracts, stories, security requirements, and test strategy must remain consistent with its acceptance criteria. The approved Section 10 deferrals are not MVP blockers. Implementation readiness is determined by the architecture and story-level gates rather than by unresolved product decisions in this PRD.
