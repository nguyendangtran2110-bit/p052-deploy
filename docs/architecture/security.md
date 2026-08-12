# MVP Security Architecture

## Security Boundaries

1. Browser input is untrusted, including role, IDs, profile fields, ticket versions, notification audiences, and external URLs.
2. FastAPI authentication/authorization middleware establishes the principal and scope before application services run.
3. PostgreSQL credentials and external-provider secrets are server-only.
4. Registry, OTP, LLM, and knowledge providers are untrusted availability and data-quality dependencies behind adapters.
5. Zalo is an untrusted external navigation target even after rule validation.
6. The public edge is the same-origin boundary: web assets and `/api/*` share one origin while FastAPI remains the only domain API.

## Authentication Controls

- Argon2id password hashing; never reversible encryption.
- Opaque random sessions in `HttpOnly`, `Secure`, `SameSite=Lax` cookies.
- CSRF token on every state-changing browser request.
- Strict production Origin validation and no credentialed cross-origin API access.
- Session rotation after login, recovery, role/status change, and privilege-sensitive events.
- Global session revocation on deactivation or credential reset.
- OTP values hashed, short-lived, attempt-limited, resend-limited, and purpose-bound.
- Rate limits for registration, login, recovery, OTP send/verify, and username/ID enumeration paths.

## Authorization Controls

- Backend-enforced RBAC plus building-floor scope on every protected query and mutation.
- Exact pair evaluation; `ALL_FLOORS` applies only within one building.
- Ticket authorization uses immutable submitted scope, not the resident's current location.
- Recheck manager scope in the same transaction as ticket transitions and notification sends.
- Refresh manager scope before scoped mutations and fail protected reads closed after the 15-minute freshness window expires.
- Increment `scope_version` and invalidate stale session/client scope whenever the registry projection changes.
- Direct object IDs and route URLs never bypass filters.
- Use existence-safe `404` responses for out-of-scope protected resources.
- Administrators receive explicit capabilities; the role does not imply blanket conversation/ticket access.

## Sensitive Data Handling

Sensitive data includes password/session/OTP material, resident/manager IDs, phone, email, location, active draft/ticket content, Zalo URL, registry records, and notification payloads.

- TLS is required outside local development.
- Protected API responses use `Cache-Control: no-store`; the edge must not cache authenticated HTML or JSON. The frontend clears protected query caches on scope/account changes.
- Managed database encryption at rest is required for deployed environments.
- Secrets come from deployment secret stores/environment injection, never committed files or frontend variables.
- Redact contact data and external URLs in logs.
- Do not log raw chat prompts, draft/ticket content, OTP values, passwords, session cookies, or provider tokens.
- Persistent draft content is stored only in PostgreSQL and returned only to its authenticated resident owner. Browser storage APIs do not persist draft fields. Account-bound `sessionStorage` may contain only non-sensitive pending-submit recovery metadata and must be purged on account switch/definitive result. Every mutation is bound to the account, immutable `draft_id` generation, and expected version; stale generations cannot affect later drafts.
- The frontend purges draft query caches and unsaved buffers on account switch. Session expiry preserves the server draft but requires reauthentication and refetch before further edits.
- Export/backup access is operationally restricted and audited.

## Input Validation

- Pydantic/API schemas enforce length, type, enum, and Unicode-safe normalization boundaries.
- Subject/content reject empty-after-trim values and enforce configured size limits.
- Urgency is enum-only: `LOW`, `NORMAL`, `HIGH`.
- Denial explanation is required, trimmed, and length-limited.
- Building/floor/unit/profile snapshot fields are server-derived.
- Zalo validation uses parsed `ZaloLinkPolicy v1` scheme/host/path allowlists; no remote existence request is performed. Revalidate stale policy versions before handoff.
- LLM output is parsed into a constrained schema; unsupported fields are discarded.
- Notification audience IDs are resolved and authorized server-side.

## Abuse Cases and Required Controls

| Abuse case | Required control |
|---|---|
| Attacker claims another resident/manager ID | Registry contact match, OTP, atomic unique claim, rate limits |
| Administrator learns or sets a user's credential | Pending activation only; user sets password after OTP; no plaintext secret returned |
| Client sends `actor_role=manager` | Ignore client role; session principal only |
| Manager combines building A with floor from building B | Exact pair grants and SQL predicates |
| Manager enumerates out-of-scope tickets | Scope-filtered lists and existence-safe object responses |
| Two managers overwrite status | Expected-version compare-and-swap; first valid write wins |
| Concurrent detail opens hide the loser | Observed version/status compare-and-swap plus idempotent conflict notification |
| Repeated submit creates duplicate tickets | Durable unique account/key-to-ticket result and same-key POST retry |
| Two sessions overwrite the same draft | Unique account row, draft-generation plus expected-version compare-and-swap, idempotent mutation, visible field-level conflict recovery |
| One account reads another account's draft | Ownership derived only from authenticated principal; no account ID selector; existence-safe response |
| Resident injects malicious Zalo URL | Local parser/allowlist/normalization; no remote fetch |
| Prompt injection asks assistant to submit or expose data | No privileged tools; constrained output; backend trust boundary |
| Broadcast audience changes after preview | Re-resolve scope at send time; require refreshed preview |
| Partial-floor manager targets an entire building | Whole-building selector requires that building's `ALL_FLOORS` grant |
| Browser XSS reads current draft buffer | CSP, output escaping, dependency review, no persistent browser draft storage |
| Deactivated manager retains session | Revoke sessions and check active account on protected requests |

## Logging and Audit

Audit:

- account creation, verification, recovery, deactivation/restoration;
- role and registry-association changes;
- manager scope projection changes;
- draft start/replace/discard/submit metadata without routine draft content;
- ticket submission/open/terminal/conflict events;
- notification campaign preview/send/fan-out failures;
- Zalo handoff attempts without raw URL; and
- administrator actions.

Operational logs use request IDs and stable error codes. Security audits store actor/resource/action/outcome metadata, not secrets or unnecessary message content.

## Current Repository Risks

The brownfield implementation must not be deployed as the approved MVP because:

- current API requests trust client-provided `actor_role`;
- `src/services/mvp.py` uses hard-coded resident data, SQLite runtime schema creation, an obsolete unscoped draft model, and obsolete states;
- no authentication, CSRF, session, or manager-scope enforcement exists; and
- `.env.example` previously contained a credential-shaped `AI_LOG_API_KEY` value and now contains a clearly fake placeholder. Treat the previous value as potentially exposed: rotate/revoke it and audit repository history/telemetry before any external deployment.

The potential exposed credential is a deployment/security blocker, not an architecture blocker. Concrete registry/OTP provider configuration is an implementation dependency; the local identity-claim and provider-neutral integration contracts are decided.

## Deferred Security Policy

Notification retention, benefit governance, chatbot source governance, quantitative performance targets, and document-upload controls are deferred by product direction. The MVP must not silently add data collection that depends on those policies.
