# Final Persistent Draft and Rule-Only Zalo Architecture Review

**Reviewer:** Winston, System Architect  
**Date:** 2026-08-11  
**Scope:** Final verification of the authoritative PRD and architecture changes for persistent account-owned ticket drafts and local rule-only Zalo validation  
**Verdict:** **PASS WITH CONCERNS**

The revised contract closes the prior data-corruption, generation-history, and ambiguous-submission blockers. Draft generations now have immutable IDs, all mutations compare account/generation/version, submission results are durable and committed with ticket creation plus draft deletion, profile/contact rows are read coherently, active-draft retention is explicit, and Zalo validation is a versioned local policy with no remote verification. Two finalization concerns remain; neither is an architecture blocker or reopens an approved deferred area.

## Prior Finding Verification

### ABA prevention with `draft_id` - PASS

The earlier ABA race is closed:

- `docs/architecture/domain-model.md:90` defines an immutable unpredictable generation ID.
- `docs/architecture/api-contracts.md:99` returns it to the client, and `docs/architecture/api-contracts.md:112` requires it on mutations.
- `docs/architecture/data-architecture.md:159` compares `(resident_account_id, draft_id, version)`.
- `docs/architecture/api-contracts.md:127` makes replace install a new generation at version `1` atomically.
- `docs/architecture/security.md:45` binds the same invariant at the trust boundary.

A stale request from a deleted/replaced generation cannot match a later draft even when both use the same version number.

### Durable same-key POST submission under PostgreSQL - PASS

The unobservable `submission_processing` protocol is removed. The replacement is internally consistent:

- `TicketSubmission` is a durable unique account/key-to-ticket mapping at `docs/architecture/domain-model.md:100`.
- The schema and ticket-history retention are defined at `docs/architecture/data-architecture.md:48`.
- One transaction locks the exact draft generation/version and coherent profile rows, creates ticket/snapshot/event, inserts the durable result, and deletes the draft at `docs/architecture/data-architecture.md:168`.
- `docs/architecture/api-contracts.md:132` requires the client to retry the same POST and key after an ambiguous transport outcome; there is no status endpoint or uncommitted `processing` state.

The database uniqueness constraint plus draft-row serialization prevents duplicate tickets. Implementations must recheck the durable mapping after any wait that ends with the draft row absent; this is already implied by the promised same-key result and should be covered by concurrency tests.

### Atomic ticket creation and draft deletion - PASS

`docs/architecture/data-architecture.md:168`, `docs/architecture/api-contracts.md:129`, and `docs/architecture/adr/ADR-0004-persistent-ticket-draft.md:18` consistently place ticket, immutable snapshot, initial event, durable submission result, and draft deletion in one PostgreSQL transaction.

### Snapshot coherence - PASS

`docs/architecture/data-architecture.md:81` requires account-contact and resident-profile rows to be locked/read in a fixed order inside the ticket transaction. This prevents a ticket from combining contact and location values from different logical profile moments.

### Cross-session/device and account isolation - PASS

- Ownership is derived exclusively from the authenticated resident at `docs/architecture/authentication-authorization.md:103`.
- Anonymous, manager, administrator, and other-account draft access is denied at `docs/architecture/api-contracts.md:88` and `docs/architecture/authentication-authorization.md:105`.
- Logout, session rotation, and another device preserve the server draft, while account switching purges protected client state at `docs/architecture/authentication-authorization.md:107`.
- The frontend buffer is account/session-epoch-bound and uses a single-flight queue at `docs/architecture/data-architecture.md:69` and `docs/architecture/frontend-architecture.md:40`.

### Persistent-draft retention - PASS

The MVP lifecycle is now explicit. `docs/architecture/data-architecture.md:187` and `docs/architecture/adr/ADR-0004-persistent-ticket-draft.md:20` state that drafts do not expire for inactivity, deactivation makes them inaccessible without deleting them, and restoration restores access. Permanent account deletion/cleanup remains outside MVP rather than being silently invented.

### Generation-gone response semantics - PASS

The contract no longer promises terminal reasons that the MVP data model cannot prove:

- `docs/architecture/data-architecture.md:164` returns generic `ticket_draft_generation_gone` when the supplied generation is no longer active.
- `docs/architecture/api-contracts.md:126` permits a same-account ticket reference only when a durable `TicketSubmission` proves that the generation was submitted.
- `docs/architecture/api-contracts.md:290` explicitly prohibits inferring the cause without durable submission evidence.
- `docs/architecture/frontend-architecture.md:69` requires the UX to say only that the draft is no longer active and never guess discarded versus replaced.

This is account-safe and implementable without a draft-history or tombstone entity. ABA safety remains provided by the immutable `draft_id`, while discarded and replaced generations intentionally leave no product-domain history in MVP.

### Rule-only Zalo policy and versioning - PASS

The Zalo boundary is executable and remains within approved scope:

- The PRD fixes `ZaloLinkPolicy v1` acceptance criteria at `docs/PRD.md:411`.
- `docs/architecture/integrations.md:124` identifies the version-controlled policy and fixture paths and defines the exact accepted syntax.
- `docs/architecture/adr/ADR-0006-rule-based-zalo-validation.md:12` defines canonicalization, rejection rules, stored validator version, and stale-policy revalidation.
- `docs/architecture/api-contracts.md:138` rechecks manager scope and stale validator versions before handoff.
- External opening uses `noopener`, `noreferrer`, and no-referrer policy; no Zalo/profile-existence request is introduced.

The implementation still needs to materialize the documented YAML and fixture files before the Zalo story is complete, as correctly classified in `docs/architecture/implementation-readiness.md:71`.

### Prototype migration and readiness - PASS WITH CONCERNS

`docs/architecture/data-architecture.md:196` classifies SQLite/demo state as disposable and prohibits migrating the obsolete drafts/tickets. `docs/architecture/deployment.md:82` requires the new uniqueness, generation, version, and durable submission-result constraints. `PASS WITH CONCERNS` is the correct overall readiness class: architecture work is substantially complete, while registry/OTP configuration, exact dependency lockfiles, credential-history remediation, UX artifacts, and implementation tests remain gated concerns.

## Finalization Notes

### F-001 - Canonical spine status: RESOLVED

`docs/architecture/ARCHITECTURE-SPINE.md` is now finalized with `status: final`, consistent with the README and implementation-readiness artifact.

### F-002 - Referenced Zalo policy/fixture artifacts are implementation story outputs

The policy is fully specified in the PRD and architecture. The absence of `config/zalo/zalo-link-policy-v1.yaml` and `tests/fixtures/zalo-link-policy-v1.json` is therefore not an architecture blocker; these are required outputs of the Zalo implementation/test story. Reviews should reject any implementation that broadens the backend policy or performs a remote existence check.

## Readiness Verdict

| Area | Verdict |
|---|---|
| Draft cardinality and account ownership | PASS |
| ABA prevention and optimistic concurrency | PASS |
| Same-key submission retry and atomic transaction | PASS |
| Snapshot coherence | PASS |
| Cross-session/device behavior | PASS |
| Anonymous/cross-role/cross-account denial | PASS |
| Retention and prototype migration | PASS |
| Rule-only Zalo boundary | PASS |
| Generic generation-gone contract | PASS |
| Overall architecture readiness | PASS WITH CONCERNS |

## Final Verdict

**PASS WITH CONCERNS.** All substantive persistent-draft and rule-only Zalo architecture defects are resolved, including the generation-gone contract. The architecture is safe to proceed into implementation planning. Materialize the specified Zalo policy and fixture files in the implementation story. Approved deferred MVP areas remain untouched.
