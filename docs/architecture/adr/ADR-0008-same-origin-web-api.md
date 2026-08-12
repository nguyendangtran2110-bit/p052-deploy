# ADR-0008: Same-Origin Web and API Boundary

**Status:** Accepted
**Date:** 2026-08-11

## Context

Opaque cookie sessions and CSRF protection require a stable browser/API topology. Earlier diagrams could be read as either direct cross-origin API access or a web-server intermediary.

## Decision

Serve the Next.js application and FastAPI API behind one public HTTPS origin. Route `/api/*` directly to FastAPI through the edge/reverse proxy. Disable credentialed CORS in production. Use `HttpOnly`, `Secure`, `SameSite=Lax` session cookies, strict Origin validation, and a session-bound synchronizer CSRF token for authenticated mutations.

Next.js route handlers do not duplicate the domain API or authorization layer.

## Rationale

- Simplifies cookie, CSRF, and local-development behavior.
- Keeps FastAPI as the one application authorization boundary.
- Avoids provider-specific cross-site cookie assumptions.

## Tradeoffs

- The edge must route both frontend and API paths consistently.
- Independent frontend/API domains require a future ADR and security review.

## Consequences

Local, CI, staging, and production exercise the same-origin path. Browser API clients always use relative `/api/v1` URLs.
