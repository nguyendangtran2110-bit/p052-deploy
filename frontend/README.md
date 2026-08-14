# OnBxrd Frontend

OnBxrd is a synthetic MVP for building onboarding and resident support. This package contains the complete Next.js frontend for Public, Resident, and Manager workflows, including scoped demo identities, same-origin mock APIs, server-owned ticket drafts, and an untrusted mock assistant.

The interface uses the Quiet Signal visual system with equal Light and Dark themes, user-controlled theme switching, reduced-motion support, and purposeful MotionSites-inspired choreography.

> **Authority:** This README is implementation guidance only. Product and technical decisions remain governed by `../docs/PRD.md`, `../docs/architecture/ARCHITECTURE-SPINE.md`, approved ADRs, canonical `../docs/frontend/*` specifications, and the active implementation artifact.

## Requirements

- Node.js 22 or newer
- npm
- Chromium for Playwright browser tests

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000/` for the public landing page, then choose Sign in or Create an account.

For a production-style local run:

```bash
npm run build
npm run start
```

The shell, routes, synthetic sign-in, tickets, and profile flows run with `npm run dev`. Homie Agent's grounded answers additionally require the repository's FastAPI RAG service; without it, the panel stays available and shows a safe unavailable response.

To use Homie Agent locally, run both servers in separate terminals:

```bash
# repository root
uvicorn src.main:app --port 8000

# frontend/
npm run dev
```

The Next.js proxy calls `http://127.0.0.1:8000/api/v1/rag/chat` by default. Set `BACKEND_API_URL` before starting Next.js if the backend uses another origin, for example `BACKEND_API_URL=http://127.0.0.1:8010 npm run dev`.

## Demo Accounts

All accounts and passphrases below are committed synthetic fixtures. They are not real credentials and must never be reused outside this demo.

| Type | Synthetic identity | Username | Passphrase | Scope |
|---|---|---|---|---|
| Resident | Avery Lagoon | `resident.lagoon` | `DEMO-LAGOON-ONLY` | Harbor House, floor 08 |
| Resident | Blake Ember | `resident.ember` | `DEMO-EMBER-ONLY` | Harbor House, floor 11 |
| Resident | Casey Harbor | `resident.harbor` | `DEMO-HARBOR-ONLY` | Orchard Annex, floor 03 |
| Manager | Drew Eight | `manager.eight` | `DEMO-EIGHT-ONLY` | Harbor House, floor 08 |
| Manager | Emery Harbor | `manager.harbor` | `DEMO-HARBOR-MGR` | Harbor House, all floors |
| Manager | Finley Orchard | `manager.orchard` | `DEMO-ORCHARD-ONLY` | Orchard Annex, floor 03 |

The login page can populate these values automatically. Different accounts in the same role intentionally see different ticket sets according to exact Resident ownership or Manager building-and-floor grants.

## Route Inventory

The MVP contains a public landing page at `/` plus exactly 18 authentication and protected workflow routes. Administrator UI is not included.

### Public (3)

- `/login`
- `/register`
- `/recovery`

`/` is the OnBxrd landing page. It uses local visual placeholders until you add images under `public/landing/`; see `public/landing/README.md` for its independent `hero`, `features`, `workflows`, and `stories` image sets.

### Resident (8)

- `/resident/onboarding`
- `/resident/benefits`
- `/resident/assistant`
- `/resident/tickets`
- `/resident/tickets/new`
- `/resident/tickets/[ticketId]`
- `/resident/notifications`
- `/resident/profile`

### Manager (7)

- `/manager/dashboard`
- `/manager/residents`
- `/manager/onboarding`
- `/manager/tickets`
- `/manager/tickets/[ticketId]`
- `/manager/notifications`
- `/manager/profile`

## Available Commands

| Command | Purpose |
|---|---|
| `npm run dev` | Start the Next.js development server |
| `npm run build` | Create the standalone production build |
| `npm run start` | Run the production build |
| `npm run typecheck` | Check TypeScript without emitting files |
| `npm run lint` | Run ESLint with zero warnings allowed |
| `npm test` | Run Vitest unit, service, route, and security tests |
| `npm run test:e2e` | Run Playwright in desktop Light and Dark projects |

Install the Playwright browser if it is not already available:

```bash
npx playwright install chromium
```

The E2E configuration starts the app at `http://127.0.0.1:3107`. Ensure that port is free before running the suite.

## Verification Baseline

The completed implementation has been verified with:

- TypeScript and ESLint checks
- Production build
- 31 Vitest tests
- 34 Playwright tests across Light and Dark themes
- All 18 routes and all six scoped identities
- 360px responsive behavior and 320 CSS px reflow
- Reduced-motion behavior and keyboard focus transitions
- Hostile mock-LLM filtering and cross-account authorization denial
- Dependency audit with no known production-package vulnerabilities

Run the main local gate with:

```bash
npm run typecheck
npm run lint
npm test
npm run build
npm run test:e2e
```

## Architecture

```text
app/                  Next.js App Router pages, layouts, and mock API routes
src/components/       Shells, accessible primitives, theme and workflow UI
src/lib/              Session, ticket contract/client, mock LLM, volatile state
src/mock/             Synthetic identities, scoped data, server-side mock stores
src/styles/           Quiet Signal tokens, themes, motion, and responsive CSS
tests/                Vitest and Playwright coverage
mock-data/*.json      Committed synthetic domain and assistant fixture content
mock-data/README.md   Fixture layout, validation, editing, and safety rules
```

Important runtime boundaries:

- Ticket draft and submitted-ticket content stays in server-side process memory, not browser persistence.
- Browser storage contains only theme, synthetic session selection, and account-bound retry metadata where required.
- Resident ticket access is owner-scoped.
- Manager ticket access is constrained by exact building and floor grants.
- Foreign or unavailable ticket IDs return existence-safe results.
- Protected Resident and Manager pages receive `Cache-Control: no-store`.
- Production responses use a per-request nonce Content Security Policy and standard hardening headers.
- Domain fixtures are statically imported from `mock-data/*.json` and validated by `src/mock/data.ts` before pages, APIs, or authorization helpers can use them.

## Homie Agent Safety

Homie Agent is the user-facing name for the grounded assistant. Residents and Managers can open its persistent shared workside panel through the same same-origin proxy. The proxy calls the local FastAPI RAG endpoint described above; it is not started by `npm run dev`. Backend output is treated as hostile and passes through the same type of trust boundary expected for a real model:

- only approved schema fields survive validation;
- HTML and unsafe URLs are rendered as inert text or rejected;
- role, identity, authorization, and server-owned context cannot be changed;
- ticket proposals are limited to Subject, Content, and Urgency;
- a proposal never submits a ticket or performs another privileged action.
- Manager conversations are grounded answer/citation only; they never receive a resident ticket proposal or ticket action.

## Accessibility and Design

- WCAG 2.2 AA-oriented implementation
- Keyboard-complete navigation, forms, tabs, dialogs, and workflow transitions
- Deterministic focus for route, stage, success, and in-place dialog changes
- Visible focus and non-color state cues in both themes
- `prefers-reduced-motion` support that removes transforms, stagger, loops, and smooth scrolling
- 360px mobile baseline and 400% zoom / 320 CSS px equivalent reflow target
- Bundled Be Vietnam Pro font with Vietnamese glyph coverage
- English-first/default interface; Vietnamese is optional/secondary

MotionSites is a visual and choreography reference only. Usability, accessibility, responsive reflow, reduced motion, task clarity, and performance take precedence.

## Demo Limitations

This package is a frontend demonstration, not a production authentication or persistence system.

- The synthetic demo identity header is intentionally forgeable.
- Mock stores are process-local and reset when the server restarts.
- Manager lifecycle and notification actions simulate service outcomes.
- No real email, phone, resident identifier, token, provider secret, or production Zalo URL is included.
- A real deployment must replace demo authentication, disable or remove mock routes and fixtures, use durable services, and authorize every operation server-side.

## Supporting Documentation

- `PRODUCT.md` - subordinate product and visual context
- `_bmad-output/implementation-artifacts/spec-redo-onbxrd-frontend.md` - completed implementation specification and verification status
- `mock-data/README.md` - fixture source, editing workflow, mock scenarios, and safety rules
- `../docs/frontend/README.md` - canonical frontend documentation index
- `../docs/frontend/ACCESSIBILITY.md` - accessibility requirements
- `../docs/architecture/ARCHITECTURE-SPINE.md` - architecture authority
