# Integrations

## Adapter Rule

External systems are accessed only through backend adapter interfaces. Domain modules consume normalized contracts and do not import provider SDKs or interpret provider-specific error bodies.

Every adapter defines timeout, retry, idempotency, redaction, and health behavior. Browser clients never receive external credentials.

## Resident and Manager Registry

### Stable `RegistryAdapter` contract

Domain/application services depend only on this normalized interface:

```text
RegistryAdapter.lookup_resident(resident_id) -> {
  registry_id,
  active,
  name,
  phone,
  email,
  building_id/number,
  floor_id/number,
  unit_id/room,
  registry_version
}

RegistryAdapter.lookup_manager(manager_id) -> {
  registry_id,
  active,
  name,
  phone,
  email,
  scope_grants: [{building_id, floor_id? , all_floors}],
  registry_version
}

RegistryAdapter.get_identity_version(role, registry_id) -> {
  active,
  registry_version
}
```

The registry is read-only for MVP. OnBxrd PostgreSQL owns the unique claim/reservation ledger and atomically commits claim plus account/profile creation after OTP verification. Registry `registry_version` is used to detect eligibility, location, or manager-scope changes; no cross-system transaction or external claimed flag is required.

The concrete implementation may use an API, database view, or versioned-file transport. Endpoint/connection details, credentials, and environment wiring are implementation configuration. Every implementation must preserve the normalized read/version behavior, stable internal IDs, consistent building-floor pairs, bounded timeouts, and stable error mapping.

Required adapter outcomes are `FOUND`, `NOT_FOUND`, `INACTIVE`, `VERSION_CHANGED`, and `UNAVAILABLE`. Provider-specific responses and records never cross the adapter boundary.

### Failure modes

- Not found/inactive: generic registration-not-eligible response.
- Already claimed locally: explicit login/recovery response approved by product.
- Timeout/unavailable before activation: no account is created; challenge/invitation remains retryable.
- Stale registry version: reload the full record before local claim activation or scope-sensitive mutation.
- Inactive identity at refresh: deny activation; for an active manager projection, remove grants and fail scoped access closed after the audited refresh.
- Local transaction failure: no session is issued; the same idempotency key safely retries or returns the committed result.

Registry maintenance ownership/workflows are deferred. A concrete transport is required before registry integration testing, but its absence does not block the architecture because the adapter and freshness contracts are stable.

## OTP and Contact Verification

### Stable `OtpService` contract

Application services depend on this provider-neutral interface:

```text
OtpService.issue_code(
  subject_ref,
  destination,
  channel,
  purpose,
  expires_in,
  idempotency_key
) -> {
  challenge_id,
  masked_destination,
  expires_at,
  retry_after
}

OtpService.verify_code(challenge_id, code) -> {
  result: VERIFIED | INVALID | EXPIRED | ATTEMPTS_EXHAUSTED,
  attempts_remaining?
}

OtpService.resend_code(challenge_id, idempotency_key) -> {
  challenge_id,
  expires_at,
  retry_after
}
```

The service sends to the server-selected registry-matching phone or email. OnBxrd owns destination selection, purpose binding, persisted challenge state, expiration, attempt/send counts, rate limits, and normalized verification result. The provider adapter may deliver an OnBxrd-generated code or use a provider-managed challenge, but this difference must not escape `OtpService`.

### Requirements

- Do not log plaintext code or full destination.
- Hash locally generated codes with a server secret.
- Use one active challenge per identity/purpose unless explicitly superseded.
- Bound resend and verification attempts.
- Use an idempotency key for send requests.
- Enforce challenge expiration server-side even if the provider has its own expiry.
- Return `retry_after` for resend/rate-limit UX; never disclose whether an unrelated identity exists.
- Provider success means accepted for delivery, not received by the user.

### Failure modes

- Provider timeout: report retryable failure; do not mark sent without confirmation.
- Duplicate provider request: return the existing challenge/send result.
- Expired/wrong code: consume an attempt and return a generic error.
- Provider outage: registration/recovery remains unavailable; existing sessions continue.
- Rate limit: return stable `otp_rate_limited` with retry timing and do not issue another active code.
- Attempts exhausted: invalidate the challenge and require a new bounded challenge.

Concrete vendor selection, credentials, sender identity, callback/polling mode, and environment wiring are implementation configuration dependencies, not architecture blockers.

## Zalo

Zalo is not an API integration in MVP. It is a browser navigation target after server-side rule validation.

### Validation boundary (`ZaloLinkPolicy v1`)

The implementation must materialize the backend policy at `config/zalo/zalo-link-policy-v1.yaml` and its accepted/rejected contract fixtures at `tests/fixtures/zalo-link-policy-v1.json`; together they are the version-controlled source of truth. MVP accepts only `https://zalo.me/<profile-id>` where `<profile-id>` is one ASCII `[A-Za-z0-9._-]{1,128}` path segment; one trailing slash is normalized away.

- Parse with a URL parser; never validate through substring checks alone.
- Require exact lowercase ASCII host `zalo.me`; reject trailing-dot or IDNA variants.
- Reject credentials, alternate schemes, explicit ports, query strings, fragments, encoded separators, malformed percent encoding, and control characters.
- Store/return the normalized URL and `validator_version=v1`.
- Re-run the same local policy on every edit and before manager handoff if the stored validator version is stale.
- Do not perform profile-existence or ownership HTTP requests.

### Manager action

The API resolves the URL from the ticket resident profile after rechecking ticket scope. The browser opens it in a new protected context with `noopener`, `noreferrer`, and no-referrer policy. If absent/invalid, the UI presents the `Notify` fallback. OnBxrd records a handoff attempt without raw URL or message content.

OnBxrd never claims profile ownership, application-open success, sent messages, delivery, or read state.

## LLM and Knowledge Retrieval

The existing Qwen/OpenAI-compatible LLM configuration and LlamaIndex/Chroma implementation remain behind `AssistantProvider` and `KnowledgeProvider` adapters.

Normalized output includes:

- grounded Vietnamese answer or unavailable response;
- source references;
- optional validated patch for subject/content/urgency; and
- missing ticket fields.

Model output is untrusted input. Validate structured patches before returning them to the client. The assistant has no privileged ticket-submit, profile-update, account, or manager-scope tool.

Provider/model selection and chatbot source governance are deferred from the architecture spine; adapter contracts remain stable.

## Retry and Idempotency Matrix

| Integration | Automatic retry | Idempotency boundary | Unsafe retry cases |
|---|---|---|---|
| Registry lookup | Short bounded retry | Request correlation | None if read-only |
| Registry version/scope refresh | Short bounded retry before failure | Identity + observed source version | Extending stale authorization after refresh is required |
| Local identity claim | Transaction retry with same key | Role + registry ID + activation key | Different identity/payload |
| OTP send | Bounded with same key | Challenge + send sequence | New code without superseding old challenge |
| LLM query | At most one safe retry before user retry | Request correlation | Ticket submission is never retried by model path |
| Knowledge lookup | Short bounded retry | Query correlation | None; return unavailable safely |
| Zalo validation | No external retry | Pure local function | Not applicable |
