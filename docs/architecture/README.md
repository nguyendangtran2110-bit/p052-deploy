# OnBxrd MVP Architecture

**Status:** Architecture complete; implementation and deployment concerns remain
**Owner:** System Architect
**Scope:** First-release resident and manager web application with administrator support
**Product authority:** [`../PRD.md`](../PRD.md) is the authoritative MVP product specification. [`../Brief.md`](../Brief.md) and [`../../PRODUCT.md`](../../PRODUCT.md) are legacy/supporting documents; where they conflict with the PRD, the PRD wins.

## Architecture Status

The architecture spine and supporting contracts are complete for review and implementation planning. The authoritative PRD now matches the architecture on rule-only Zalo validation and a zero-or-one persistent account-owned ticket draft. Registry and OTP transport/provider details are implementation configuration dependencies. The credential hygiene item blocks external deployment only.

## Document Map

| Document | Purpose |
|---|---|
| [`ARCHITECTURE-SPINE.md`](ARCHITECTURE-SPINE.md) | Canonical invariants and dependency rules |
| [`system-context.md`](system-context.md) | System boundary, actors, trust boundaries, and external dependencies |
| [`container-architecture.md`](container-architecture.md) | Runtime containers and module ownership |
| [`domain-model.md`](domain-model.md) | Entities, ownership, relationships, and ticket lifecycle |
| [`data-architecture.md`](data-architecture.md) | Persistent/transient data, snapshots, scope, and retention assumptions |
| [`authentication-authorization.md`](authentication-authorization.md) | Registration, OTP verification, sessions, RBAC, and manager scope |
| [`api-contracts.md`](api-contracts.md) | API responsibilities, errors, idempotency, and concurrency |
| [`integrations.md`](integrations.md) | Registry, OTP, Zalo, LLM, and knowledge boundaries |
| [`security.md`](security.md) | MVP security controls and abuse cases |
| [`frontend-architecture.md`](frontend-architecture.md) | Role shells, route boundaries, persistent draft UX, and accessibility |
| [`deployment.md`](deployment.md) | Environments, topology, configuration, health, and rollback |
| [`implementation-readiness.md`](implementation-readiness.md) | Blockers, deferred items, and implementation order |
| [`adr/`](adr/) | Material architectural decisions and tradeoffs |
| [`reviews/review-resolution.md`](reviews/review-resolution.md) | PM/Architect/UX findings and final disposition |

## Authority and Legacy Documents

The files in this directory are authoritative for the technical architecture after product requirements are read from [`../PRD.md`](../PRD.md). Legacy wording in [`../Brief.md`](../Brief.md) and [`../../PRODUCT.md`](../../PRODUCT.md) is supporting context only and cannot override the PRD; it does not need reconciliation for architecture approval. Actual contradictory requirements inside the PRD must be reconciled by PM and Architect before architecture approval or affected story execution.

The previous [`ARCHITECTURE.md`](ARCHITECTURE.md), [`architecture_diagram.md`](architecture_diagram.md), and [`uiFlow.mermaid`](uiFlow.mermaid) are compatibility pointers/updated views. Existing [`docs/api.md`](../api.md) and [`docs/deployment.md`](../deployment.md) describe the superseded demo and must not be used as implementation authority.

## Explicitly Deferred from MVP Architecture

- Benefit governance and content ownership workflow.
- Chatbot source governance, update ownership, and escalation policy.
- Notification type catalog beyond the extensible type field, plus retention policy.
- Manager-registry maintenance ownership, staffing, and authoring workflow. Runtime projection refresh and revocation behavior are defined because authorization depends on them.
- KPI targets and pilot thresholds.
- Quantitative performance, availability, and capacity targets.
- Document upload and document-retention workflow.
- External notification channels and live Zalo messaging, including profile-existence/ownership verification.
