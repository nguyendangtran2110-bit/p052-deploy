# ADR-0006: Rule-Based Zalo URL Validation Only

**Status:** Accepted
**Date:** 2026-08-11

## Context

Residents provide Zalo profile links and managers need a direct `Zalo` action. Reliable profile-existence verification may not be available, and OnBxrd does not control the manager's Zalo account or message outcome.

## Decision

Validate Zalo URLs locally with version-controlled `ZaloLinkPolicy v1`: `https`, exact ASCII host `zalo.me`, and exactly one `[A-Za-z0-9._-]{1,128}` profile-ID path segment, with an optional trailing slash normalized away. Reject user-info, explicit ports, query strings, fragments, trailing-dot/IDNA host variants, encoded separators, malformed percent encoding, and control characters. Store the normalized URL with `validator_version=v1`; revalidate on edit and before manager handoff when the stored version is stale. Do not perform remote existence/ownership checks. Return the normalized URL only after ticket-scope authorization.

If no valid URL exists, keep the action visible and offer the `Notify` fallback. Record only a redacted handoff attempt.

## Rationale

- Meets the approved fallback decision without depending on an unsupported provider API.
- Eliminates server-side remote fetch and associated SSRF/availability risks.
- Keeps product claims honest about what OnBxrd can observe.

## Tradeoffs

- A syntactically valid link may not exist or may not belong to the resident.
- Managers may encounter an external error after handoff.
- Product copy must use `validated link`, not `verified profile`.

## Consequences

No Zalo SDK, message API, delivery tracking, group monitoring, or profile-existence service is part of MVP. `config/zalo/zalo-link-policy-v1.yaml` and `tests/fixtures/zalo-link-policy-v1.json` are the implementation validation source of truth; frontend validation may assist but cannot broaden it.
