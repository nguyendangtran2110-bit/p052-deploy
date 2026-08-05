# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- Primary: residents of one Vietnamese condominium building, especially new owners and tenants completing post-handover onboarding.
- Secondary: the building's property-management staff, who oversee resident progress and support requests.

## Product Purpose

OnBxrd is an agent-assisted resident onboarding and building-support system. It replaces fragmented calls, informal chat, paper checklists, and opaque defect follow-up with a guided, traceable web experience.

For the MVP demo, a resident completes onboarding, gets source-cited answers about the building, submits a reviewed support request, and follows its resolution. Management can review, act on, and audit every request.

## Positioning

OnBxrd combines a persistent onboarding checklist, building-scoped RAG answers with citations, and human-confirmed ticket drafting from both the web app and an official Zalo OA-managed group. The web app remains the source of truth; the agent never submits a ticket without an explicit resident confirmation.

## Operating Context

- The initial demo audience is a single condominium building in Vietnam.
- Residents use the web app during and after unit handover to understand building policies, finish onboarding tasks, and request support.
- Management operates approval, resident-progress, ticket, digest, and reporting views.
- Official building documents are ingested for answers; each answer must identify its source document and section or chunk.
- An OA-owned Zalo GMF group is the supported group-chat integration. Webhooks and recoverable conversation backfill supply messages for digestion and issue-draft workflows.

## Capabilities and Constraints

- The MVP stack is Next.js/React, FastAPI, LangGraph deterministic workflows, PostgreSQL with pgvector, and Dockerized local deployment.
- Residents and managers have separate backend-enforced permissions.
- Ticket lifecycle: `DRAFT → SUBMITTED → APPROVED → IN_PROGRESS → RESOLVED`, with `REJECTED` available from `SUBMITTED`. Rejections require a reason; resolutions require a note; all mutations are audited.
- The agent may create a ticket draft and suggest priority, but a resident must review, edit if needed, and explicitly submit it.
- Zalo support is limited to verified OA + OA-owned GMF capabilities. Arbitrary personal/group-chat reading and unofficial client automation are explicitly out of scope.
- A dependency-injected mock Zalo adapter and realistic fixtures keep the demo runnable without live credentials. Simulated channel activity must be clearly labeled.
- Protect Zalo identifiers, phone numbers, tokens, and sensitive message data. Identity linkage requires consent and verification.
- Do not fabricate building policies: answers must be grounded in the active building's documents or clearly say information is unavailable.
- The canonical product name is **OnBxrd**. Use this name in new product copy and interface labels.

## Brand Commitments

- OnBxrd is the product name. MoveIn is legacy wireframe evidence, not the product name for new work.
- Supplied resident and building-manager wireframes are real interface evidence to preserve when implementing surfaces.
- No additional brand voice, visual identity, or naming rules have been confirmed.

## Evidence on Hand

- Product brief: `docs/Brief.md`.
- Product requirements: `docs/PRD.md`.
- Repository-wide MVP scope and acceptance criteria: `AGENTS.md`.
- Resident wireframes: `docs/wireframe/Resident1.png` through `docs/wireframe/Resident4.png`.
- Building-management wireframes: `docs/wireframe/BuildingManager1.png` through `docs/wireframe/BuildingManager3.png`.
- These materials establish product and implementation evidence; they do not authorize invented policies, metrics, testimonials, or external integration claims.

## Product Principles

1. Ground every building-policy answer in the correct building's current source material and show the citation.
2. Keep residents in control of support requests: assistance drafts, people confirm and submit.
3. Make management actions accountable through explicit permissions, required reasons or notes, and auditable history.
4. Use Zalo to extend a web-owned workflow, never as an unsupported surveillance channel or ticket system of record.
5. Favor a reliable, demonstrable vertical slice for one building over premature multi-property breadth.

## Accessibility & Inclusion

- The desktop-first demo must not break below tablet width.
- Status cannot rely on color alone.
- Important results remain visible in the page; toasts are supplemental.
- Required states include loading, empty, error, and permission-denied states.
