# Authentication and Authorization

## Authentication Model

Use first-party username/password authentication with opaque, database-backed sessions carried in `HttpOnly`, `Secure`, `SameSite=Lax` cookies. Session tokens are random bearer secrets; PostgreSQL stores only a hash plus account, expiry, and revocation metadata.

The browser and API share one public origin. `/api/*` is reverse-proxied to FastAPI, production credentialed CORS is disabled, and authenticated mutations require a synchronizer CSRF token bound to the session plus an allowed `Origin` check.

Passwords are hashed with Argon2id using deployment-reviewed parameters. Passwords, OTP values, registry contact values, and session tokens must never appear in application logs.

## Resident Registration

1. Resident submits immutable username, password, phone, email, and resident ID.
2. API normalizes inputs and looks up an active resident registry record plus the local OnBxrd claim/reservation state.
3. At least one submitted contact channel must match the registry record.
4. The server selects one matching channel, creates a bounded registration challenge, sends a one-time code, and returns only its masked destination.
5. Resident submits the code.
6. In one PostgreSQL transaction, the API verifies the challenge state, activates the unique local identity claim, creates the account/profile, copies the current registry location projection/version, and records session issuance metadata.
7. After commit, the API issues the session cookie. The external registry is not mutated and is not part of the transaction.
8. Account activation is reflected as completed in onboarding.

If the ID is already claimed, return a claimed-ID response that directs the user to login or account recovery. Do not create a second account.

## Manager Registration

Manager registration follows the same flow using manager ID. Successful claim creates the manager account/profile and imports the registry-provided building-floor grants, including per-building `ALL_FLOORS` grants, with the registry source version and check timestamp.

No manager-supplied building/floor data is accepted. A manager with no resolved grants may authenticate but receives an empty scoped experience and cannot access resident resources.

## Administrator Provisioning

- There is no public administrator registration endpoint.
- The first administrator is provisioned through a controlled operational command or migration using a secret input outside source control.
- Administrators create resident/manager pending activation invitations against an active registry identity. This reserves the local claim but creates no active credentials or session.
- The invited person uses the normal registration form, completes matching-contact OTP verification, and chooses immutable username/password. A matching pending invitation is consumed in the same local transaction as account activation.
- Administrators never choose, receive, display, or transmit a user's password or OTP. Duplicate ID/username behavior remains the same as self-registration.
- Invitations have expiry/cancel states and idempotent audited cleanup. Expiry releases only an unused reservation.
- Creating additional administrators, permanent deletion, and elevated content access remain outside the approved MVP capability unless separately authorized.

## Login, Logout, and Recovery

- Login uses username and password and creates a new opaque session.
- Logout revokes the server-side session and clears the cookie/client caches; it does not delete the resident's persistent ticket draft.
- Account deactivation revokes all sessions.
- Recovery verifies a current account-owned verified phone/email before password reset. Registry contact is used only before activation or through an explicit administrator-assisted recovery path; it is not silently copied over an owner-updated verified contact.
- Username and registry ID are immutable.

## Profile and Credential Edit Matrix

| Field | Resident owner | Manager owner | Administrator | Verification/effect |
|---|---|---|---|---|
| Username | Read-only | Read-only | Read-only after activation | Immutable unique identity |
| Resident/manager ID | Read-only | Read-only | Read-only after claim | Immutable registry association |
| Display name | Edit | Edit | Correct with audit | Used for future display/snapshots only |
| Phone | Replace | Replace | Initiate correction only | Current password/recent auth plus OTP to new phone; becomes recovery and future ticket-snapshot phone |
| Email | Replace | Replace | Initiate correction only | Current password/recent auth plus OTP to new email; becomes recovery contact |
| Password | Change | Change | Initiate reset only | Current password/recent auth; revoke all other sessions and rotate current session |
| Resident building/floor/room | Read-only | Not applicable | Registry refresh/correct with audit | Never rewrites old tickets |
| Manager building/floor grants | Not applicable | Read-only | Trigger registry refresh with audit | No arbitrary owner-supplied or cross-paired scope |
| Zalo URL | Edit | Not applicable | No default capability | Local rule validation; no existence claim |
| Theme/preferences | Edit | Edit | No default capability | Account-scoped presentation only |

Registry verification contacts are retained as source evidence/versioned snapshots and are never edited through profile APIs. Account phone/email are the current verified contacts. Profiles do not store duplicate authoritative contact fields.

## RBAC

| Capability | Resident | Manager | Administrator |
|---|---:|---:|---:|
| Own profile/onboarding/draft/tickets/notifications | Yes | No | Explicit admin capability only; no draft-content access by default |
| Scoped resident/onboarding/ticket reads | No | Yes | Explicit admin capability only |
| Ticket status mutation | No | Scoped manager | No by default |
| Ticket `Zalo`/`Notify` actions | No | Scoped manager | No by default |
| Targeted management notification | No | Scoped manager | No by default |
| Account lifecycle/correction | No | No | Yes for resident/manager accounts |
| Manager assignment editing | No | No | Registry refresh/correction only; registry projection controls values |

## Manager Scope Enforcement

Authorization uses server-resolved grants only:

```text
allowed = manager_has(
  resource.building_id,
  resource.floor_id
) OR manager_has(resource.building_id, ALL_FLOORS)
```

For current resident/onboarding views, use the current resident profile scope. For tickets, use the immutable submitted ticket scope. Every list query applies the same predicate in SQL; object-level checks repeat it before mutation.

New manager accounts can see older tickets when current grants match the ticket snapshot.

### Projection freshness

- Refresh the manager registry projection at login, session renewal, and before every scoped mutation, including ticket open/transition, Zalo URL retrieval, and notification preview/send.
- Scope-sensitive reads may use a successfully checked projection for at most 15 minutes. After that window, refresh before returning protected data.
- If a required refresh fails, fail closed with a stable dependency-unavailable response; do not extend stale scope. The authenticated shell may remain available without protected resident data.
- A changed registry version replaces the local grant projection transactionally, increments `scope_version`, audits added/removed grants, and makes removed scope ineffective immediately.
- A request whose session/client scope version is stale receives `scope_changed`; the client purges protected caches and reloads `/auth/me`. If no grants remain, show the empty scoped experience.
- The registry-maintenance organization and authoring workflow remain deferred; this consumption/freshness rule is mandatory.

## Ticket Draft Authorization

- Draft ownership is always derived from the authenticated resident account; request bodies and route parameters never select another account's draft.
- Draft mutations must also present the server-issued `draft_id` generation and expected version; an old generation is rejected even if a later draft exists for the same account.
- Only active resident accounts can start, read, update, replace, discard, or submit a ticket draft.
- Anonymous, manager, and administrator sessions have no draft endpoint capability by default.
- Logout/login, session rotation, and a new device preserve access because ownership belongs to the account, not a session.
- Account switch purges frontend draft caches before the next account's draft is requested.
- Account-bound pending-submit recovery metadata is restored only after `/auth/me` confirms the same account; it is purged before a different account renders.
- Deactivation blocks draft access; restoration returns access to the same account-owned draft unless it was explicitly discarded or submitted.
- Session expiry freezes any unsaved client buffer until `/auth/me` confirms the same account; the client then rebinds it to the new session epoch. A different account is rendered only after that buffer is purged.

## Trust-Boundary Rules

- Ignore `actor_role`, resident ID, manager ID, building, floor, and unit supplied as authorization claims in normal product requests.
- Derive the authenticated principal from the session cookie.
- Return `404` rather than existence-revealing `403` for out-of-scope protected objects where disclosure itself is sensitive.
- Recheck scope inside the same transaction as each ticket or notification mutation.
- Require the request/session scope version to match the refreshed local projection before scoped mutation.
- Registration endpoints apply rate limits by normalized identity, contact, IP, and device/session signals.
- OTP challenge status, attempts, and expiry are server-owned.

## Required Integration Input

Registration implementation depends on a concrete registry transport and OTP provider/environment configuration, but the stable adapter contracts are defined in [`integrations.md`](integrations.md). Atomic account claim is local to PostgreSQL and does not require an external registry transaction. These are implementation dependencies, not architecture blockers or deferred registry-maintenance governance.
