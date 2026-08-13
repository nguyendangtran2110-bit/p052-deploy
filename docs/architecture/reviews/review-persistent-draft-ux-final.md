# Persistent Draft UX Final Review

**Reviewer:** Sally, UX Designer  
**Review scope:** Final verification of direct-resume accessibility behavior, canonical assistant fingerprinting, and hard-reload-safe submission retry.  
**Verdict:** **PASS.** All three final UX seams are resolved: direct-resume accessibility behavior, canonical assistant fingerprinting, and hard-reload-safe ambiguous submission recovery.

## Resolved Verification

### UX-FINAL-001 - Direct resume versus explicit new ticket: RESOLVED

The interaction matrix now has separate rows for `Explicit New ticket with existing draft` and `Direct resume of active draft`. Direct continuation focuses the editor without a replacement dialog; only explicit new-ticket intent opens the resume/replace dialog. This is consistent with the route rules and WCAG focus behavior ([frontend-architecture.md](../frontend-architecture.md), Start, resume, and replace; Accessibility Contract).

### UX-FINAL-002 - Canonical assistant fingerprint: RESOLVED

The API now defines the assistant request context and a canonical base64url SHA-256 fingerprint over NFC-normalized subject, content, and urgency using a literal unit separator. Both sides can compute and compare the same value, so assistant proposals can reliably detect changed fields ([api-contracts.md](../api-contracts.md), Assistant Surface).

### UX-FINAL-003 - Hard-reload-safe ambiguous submission: RESOLVED

Before submit, the frontend stores only non-sensitive, account-bound attempt metadata in `sessionStorage`: account ID, `draft_id`, expected version, canonical fingerprint, idempotency key, and start time. It stores no ticket, profile, or location fields. After reload, `/auth/me` must confirm the same account before the attempt is restored; another account purges it before protected rendering ([frontend-architecture.md](../frontend-architecture.md), State Ownership and Persistent Ticket Draft; [data-architecture.md](../data-architecture.md), Frontend edit buffer).

The submit endpoint checks the durable account/key result before requiring an active draft. Therefore, when the original request committed and deleted the draft, replaying the same request/key returns the original ticket. Definitive results and account switches clear the recovery metadata ([api-contracts.md](../api-contracts.md), submission contract). This closes the hard-reload seam without persisting editable draft content in the browser.
