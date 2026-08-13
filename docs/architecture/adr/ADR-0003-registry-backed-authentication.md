# ADR-0003: Registry-Backed Self-Registration and Opaque Sessions

**Status:** Accepted
**Date:** 2026-08-11

## Context

Residents and managers self-register with username, password, phone, email, and a resident/manager ID. Outsiders must not claim identities. The ID also determines resident location or manager scope. Administrator accounts cannot use normal registration.

## Decision

- Match the submitted identity ID to an active registry record.
- Require at least one submitted contact channel to match the record.
- Verify that channel using a one-time code.
- Keep the external registry read-only and store the unique identity claim in OnBxrd PostgreSQL.
- Atomically activate the local claim and create the account/profile after OTP verification; issue the session only after commit.
- Derive resident location or manager scope from the registry record.
- Administrator account creation reserves a pending invitation; the user completes OTP and chooses credentials. Administrators never know the password.
- Keep registry verification contacts separate from current verified account contacts.
- Use Argon2id password hashes and opaque database-backed web sessions.
- Provision the initial administrator out of band; expose no public admin registration.

## Rationale

- Prevents ID-only account takeover.
- Makes scope/location server-derived.
- Database sessions make deactivation and recovery revocation straightforward.
- An opaque cookie avoids exposing role/scope claims that can become stale.

## Tradeoffs

- Registration depends on registry and OTP availability.
- Each authenticated request incurs session/account lookup cost.
- Registry lookup/version and scope-freshness behavior need a concrete integration transport.

## Consequences

Authentication implementation is blocked until registry and OTP provider contracts are supplied. No distributed transaction with the registry is required. Client-provided roles, building/floor values, and identity associations are ignored as authority.
