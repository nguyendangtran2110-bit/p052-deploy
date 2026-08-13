# PRODUCT BRIEF: OnBxrd

- **Domain:** PropTech / Resident Experience
- **Project ID:** BDSO2O-10
- **Status:** Draft - Product Vision Reset
- **Updated:** August 11, 2026
- **Form Factor:** Web application
- **Language:** Vietnamese required; English optional

---

## 1. Executive Summary

OnBxrd is a resident-services web application for two primary actors: residents and building managers. A supporting administrator role controls account access and permissions. The product helps residents understand what they need to do after moving in, discover the services and benefits available to them, get reliable answers about living in the building, request support, and receive relevant updates.

For managers, OnBxrd provides visibility into resident onboarding, a structured ticket workflow, and targeted communication tools. The product replaces fragmented instructions, hidden resident benefits, repetitive questions, informal support requests, and broad untargeted announcements with one traceable service workflow.

## 2. The Problem

Residents often receive important information through disconnected channels and at different times. They may not know:

- which move-in steps remain incomplete;
- which facilities, services, or benefits their resident identity gives them access to;
- where to find authoritative regulations and building guidance;
- how to submit a complete support request or follow its outcome; or
- whether a message from management applies to the entire building, their floor, their room, or only them.

Managers face the corresponding operational problem: limited visibility into onboarding progress, incomplete or unstructured support requests, repetitive resident questions, and no reliable way to target communications without creating notification noise.

## 3. Product Actors

### Resident

A verified building resident who uses OnBxrd during move-in and throughout their stay. Residents need guided tasks, clear benefit information, trustworthy answers, a low-friction ticket process, and relevant notifications.

### Manager

A building-management staff member who monitors onboarding progress, processes resident tickets, communicates with residents, and sends targeted notifications within their assigned scope. Each manager has a profile containing one or more assigned buildings and the floors assigned to them within each building.

### Administrator

A privileged support role responsible for account creation, deactivation, role assignment, and access control. The final administrator permission model is not yet defined.

## 4. Resident Experience

### 4.1 Guided Onboarding

Residents receive a visible, progress-based onboarding plan. Initial examples include:

- create or activate an OnBxrd account;
- join the official Zalo group using a provided link;
- complete required documentation, once those requirements are confirmed; and
- complete additional building-specific steps added as resident and management research continues.

The onboarding model must be configurable so the team can add, reorder, revise, or retire steps without redesigning the resident experience. Incomplete onboarding generates automated reminders on a controlled schedule; managers do not manually trigger reminders.

### 4.2 Resident Benefits and Entitlements

Residents can see the facilities, services, and benefits available to them based on their verified resident identity, such as pool or gym access. Each item should explain eligibility, conditions, operating information, and how to use the benefit. The experience should resemble the onboarding checklist: clear, discoverable, and actionable rather than buried in documents.

### 4.3 Vietnamese-First Resident Assistant

The chatbot answers questions about onboarding, resident benefits, regulations, rules, facilities, and other approved building information. It supports residents during onboarding and remains useful throughout their stay.

Vietnamese support is required. English support is optional for the first release. Answers must be based on approved building information; when approved sources do not support an answer, the chatbot should say so rather than inventing one.

### 4.4 Manual and Chat-Assisted Ticket Creation

Residents can start a ticket in either of two ways:

1. Open the ticket form directly.
2. Describe the problem to the chatbot, which prepares the same ticket form.

Both paths use one canonical ticket draft and one submission page. Resident profile fields such as name, room, and phone number are prefilled. When the chatbot starts the draft, it extracts relevant details from the conversation, asks follow-up questions for missing required fields, and then sends the resident to the ticket page to review and submit.

If a resident has already entered information manually and then asks the chatbot for help, the assistant should fill empty fields and propose changes to existing fields rather than silently overwrite resident input. The resident always reviews the final form and explicitly submits the ticket; the chatbot never submits it automatically.

### 4.5 Profile and History

Residents can view and edit permitted profile information, review ticket history, and change interface preferences such as theme. Verified identity fields may require a controlled correction process rather than unrestricted editing.

Residents may provide a Zalo profile link as part of their profile. OnBxrd validates that the value is a Zalo link and verifies that the referenced profile exists before exposing it to an authorized manager.

### 4.6 Notifications

Residents receive notifications for:

- ticket updates and manager responses;
- targeted management announcements;
- automated onboarding reminders; and
- problems with documentation, credentials, or account verification.

Notifications may target the entire building, a floor, a room or unit, or an individual resident. Delivery channels beyond the web application are not yet decided.

## 5. Manager Experience

### 5.1 Manager Profile and Scope

Managers have profiles that show their identity and access assignments. Assignments are grouped by building, with the permitted floors listed for each building. A manager may belong to multiple buildings and have different floor coverage in each one. The profile is the source OnBxrd uses to filter resident, ticket, and notification access.

### 5.2 Onboarding Progress

Managers can view onboarding progress for residents within the building and floor assignments on their profile and identify incomplete or blocked steps. Reminder delivery is automated when a resident creates an account and at controlled intervals while onboarding remains incomplete. Managers do not receive a manual reminder button, reducing duplicate or excessive notifications.

### 5.3 Ticket Management

Managers can open a ticket to view its details, contact the resident through Zalo or an OnBxrd notification, and move the request through its lifecycle:

- **Pending:** submitted by the resident and awaiting manager action;
- **Resolving:** accepted and actively being handled;
- **Resolved:** completed successfully; or
- **Denied:** declined with an explanation.

Opening a ticket and changing its status should be treated as separate actions until the team explicitly decides otherwise. The PM recommendation is to require an intentional Claim or Start Resolving action before the status changes.

When a verified resident Zalo profile is available, the ticket detail shows a **Zalo** button that opens that resident's Zalo profile. OnBxrd does not control which Zalo account the manager uses or claim that a message was sent. If no verified Zalo link exists, the product shows a clear popup recommending an OnBxrd notification instead.

Each manager account has its own access scope. A manager may be assigned to multiple buildings and different floors within each building. They receive and can view only tickets and residents located within those assignments. The assignments are displayed in the manager profile and cannot be changed by the manager.

### 5.4 Targeted Notifications

Managers can compose a notification with a subject, content, and defined audience. Audience targeting may include an assigned building, an assigned floor, a room or unit within that scope, or selected in-scope residents. Managers cannot target residents outside the assignments on their profile. The product should make the intended recipients clear before sending and retain an auditable record of the message.

## 6. Administrator Experience

The first administrator capability should be deliberately narrow:

- create, invite, deactivate, and restore accounts;
- assign resident, manager, and administrator roles;
- associate residents with the correct building and unit; and
- assist with account recovery and identity corrections.

Permanent deletion, permission delegation, data access, and other elevated privileges remain open decisions. Deactivation with an audit trail is preferred over immediate permanent deletion.

## 7. Product Principles

1. **Resident-controlled submission:** automation may prepare a ticket, but only the resident submits it.
2. **One workflow across entry points:** manual forms and chatbot assistance operate on the same ticket draft and validation rules.
3. **Vietnamese first:** the core experience must work naturally in Vietnamese.
4. **Verified and scoped access:** outsiders must not be able to claim resident or manager privileges using a guessable identifier, and managers can access only residents and tickets within their profile assignments.
5. **Source transparency:** building guidance must come from approved, current information.
6. **Configuration over hard-coding:** onboarding steps, benefits, targeting groups, and content will evolve.
7. **Relevant communication:** automation and targeting should reduce notification noise rather than amplify it.
8. **Verified external contact:** resident-provided external profile links are validated and scoped before managers can use them.

## 8. First-Release Scope

### Confirmed In Scope

- Resident and manager web experiences with role-based and profile-scoped access.
- Secure resident account activation using a building-issued identity or unique identifier plus additional verification.
- Configurable onboarding steps and progress tracking.
- Resident benefit and entitlement discovery.
- Vietnamese-first chatbot for approved building information.
- Manual and chat-assisted ticket drafting through one resident-reviewed form.
- Resident profile, preferences, and ticket history.
- Resident Zalo profile-link validation and the manager ticket-level Zalo action.
- Automated onboarding reminders and targeted notifications.
- Manager onboarding oversight, ticket handling, resident messaging, and notification composition.
- Manager profiles with one or more building assignments and per-building floor assignments that scope resident, ticket, and notification access.
- Minimum administrator account and role management.

### Not Yet Confirmed

- The exact onboarding documentation and whether documents are uploaded, acknowledged, or verified offline.
- English-language parity.
- Notification delivery through email, SMS, or browser push beyond the confirmed OnBxrd notification channel.
- Live Zalo message ingestion or group monitoring; the confirmed onboarding need is currently only a join link.
- Manager self-registration.
- Advanced administrator permissions and permanent deletion.
- Ticket escalation, reopening, cancellation, attachments, and service-level targets.

## 9. Success Signals

The PRD should define measurable targets after baselines and operating rules are known. The brief currently establishes the signals that matter:

- residents complete required onboarding steps with fewer support interventions;
- residents discover and use benefits they are eligible for;
- chatbot answers resolve common questions using approved information;
- residents successfully submit complete tickets through either entry path;
- managers see only the residents and tickets relevant to their assigned buildings and floors;
- targeted notifications reach the intended residents without excessive repetition; and
- outsiders cannot gain resident or manager access.

## 10. Decisions to Resolve Before Updating the PRD

1. **Resident account verification:** Use the resident identity number only as a lookup key, not as the sole credential. Recommended first release: match it against a management-owned resident registry and require a one-time activation code or verified phone/email challenge.
2. **Manager accounts:** Use administrator-issued invitations for the first release. Manager self-registration introduces a high-risk privilege-escalation path and should wait until a trusted manager registry and verification process exist.
3. **Administrator permissions:** Start with account lifecycle, role assignment, building/unit association, recovery, and audit access. Define any ability to read resident conversations, documents, or ticket content separately rather than granting blanket access.
4. **Onboarding documentation:** Model onboarding as configurable step types, such as instruction, external link, acknowledgment, form, upload, or offline verification. Do not commit to document upload until the team identifies each document, its owner, completion evidence, correction flow, and retention requirement.
5. **Benefits ownership:** Identify who maintains benefit eligibility, hours, conditions, and source information. Recommended model: building-scoped benefit records with eligibility rules and an accountable manager or administrator owner.
6. **Hybrid chatbot and form state:** Store one server-side ticket draft that both the chatbot and form update. Track the source of each field, preserve unsaved progress, fill blanks by default, and require confirmation before replacing resident-entered information.
7. **Ticket transition trigger:** Do not change Pending to Resolving merely because a manager viewed the ticket. Use an explicit Start Resolving or Claim action; require a reason for Denied and a completion note for Resolved.
8. **Ticket schema:** Confirm required fields such as category, location, description, urgency, attachments, contact preference, and access availability. The chatbot cannot reliably collect missing information until this schema is approved.
9. **Profile editing:** Separate user-editable preferences from verified identity data. Theme and contact preferences can be edited freely; room, resident identity, and possibly phone number should require verification or an administrative correction flow.
10. **Notification policy:** Define channels, mandatory versus optional categories, throttling, deduplication, quiet hours, recipient previews, delivery failure behavior, and audit retention. Automated reminders should stop immediately when onboarding is complete.
11. **Manager assignment authority:** Define who maintains manager building and floor assignments, how externally decided assignments are supplied and refreshed, and how access is revoked when a manager's real-world responsibilities change.
12. **Zalo verification mechanism:** Define the supported rule-based link validation and profile-existence check, including provider/API limits, retry behavior, and re-verification when a link changes.
13. **Chatbot source boundaries:** Define the approved content owners, document update process, source precedence, unavailable-answer behavior, and escalation path to management.

---

This brief intentionally leaves unresolved product decisions visible. Those decisions should be answered before the PRD defines detailed workflows, acceptance criteria, API contracts, and measurable targets.
